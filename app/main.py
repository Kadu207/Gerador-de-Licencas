from __future__ import annotations

import json
import os
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api_v1 import router as api_v1_router
from app.auth import create_access_token, decode_token, hash_password, verify_password
from app.config import settings
from app.infra.receita import fetch_cnpj_receita, validate_document
from app.infra.stripe_payments import create_checkout_session, stripe_enabled
from app.infra.viacep import fetch_address_by_cep
from app.jobs.alerts import run_license_alerts
from app.dashboard_stats import build_dashboard_stats
from app.licensing import PAYMENT_PLAN_LABELS, PERIOD_LABELS, PRODUCT_LABELS, STATUS_CANCELLED
from app.models import Client, LicenseRecord, Notification, Operator, Payment, SessionLocal, init_db
from app.services import (
    cancel_client,
    create_client,
    effective_for_license,
    issue_license,
    log_action,
    refresh_all_licenses,
    renew_license,
    revoke_license,
    summarize_client_licenses,
)
from app.sync import ensure_remote_tables, test_connections

ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(ROOT / "templates"))
templates.env.filters["tojson"] = json.dumps

app = FastAPI(
    title="Gerador de Licenças — Inova TI",
    version="2.0.0",
    description="API central de licenciamento para Excellence Cloud, Dental Lab e VDE Incorporadora.",
)
app.include_router(api_v1_router)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


def _cookie_secure() -> bool:
    if settings.trust_proxy:
        return True
    return settings.public_base_url.lower().startswith("https://")


@app.get("/health")
@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "gerenciador-licencas",
        "version": "2.0.0",
        "publicUrl": settings.public_base_url or None,
        "productApiConfigured": bool((settings.product_api_key or "").strip()),
        "stripeConfigured": stripe_enabled(),
        "database": "postgres" if "postgresql" in settings.local_database_url else "sqlite",
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    accept = (request.headers.get("accept") or "").lower()
    wants_html = "text/html" in accept or request.url.path.startswith(
        ("/", "/dashboard", "/clients", "/app")
    )
    if exc.status_code == 401 and wants_html and request.url.path not in {"/login", "/app/login"}:
        return RedirectResponse("/app/login", status_code=303)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


scheduler = BackgroundScheduler()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    session_token: str | None = Cookie(default=None, alias="session_token"),
    db: Session = Depends(get_db),
) -> Operator:
    token = session_token or request.headers.get("Authorization", "").replace("Bearer ", "")
    username = decode_token(token) if token else None
    if not username:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = db.query(Operator).filter(Operator.username == username, Operator.ativo.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    return user


def optional_user(
    session_token: str | None = Cookie(default=None, alias="session_token"),
    db: Session = Depends(get_db),
):
    if not session_token:
        return None
    username = decode_token(session_token)
    if not username:
        return None
    return db.query(Operator).filter(Operator.username == username, Operator.ativo.is_(True)).first()


@app.on_event("startup")
def startup() -> None:
    init_db()
    if settings.sync_remote_enabled and (
        settings.erp_database_url.strip() or settings.lab_database_url.strip()
    ):
        try:
            ensure_remote_tables()
            print("[startup] Sync remoto habilitado — tabelas ERP/Lab verificadas.")
        except Exception as exc:
            print(f"[startup] Aviso: sync remoto falhou: {exc}")
    else:
        print("[startup] API como fonte da verdade — sync ERP/Lab desligado por padrão.")

    db = SessionLocal()
    try:
        if not db.query(Operator).first():
            db.add(
                Operator(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                    nome="Administrador",
                )
            )
            db.commit()
            print(f"[bootstrap] Operador criado: {settings.admin_username}")
    finally:
        db.close()

    def job_refresh():
        db = SessionLocal()
        try:
            n = refresh_all_licenses(db)
            print(f"[scheduler] {n} licença(s) reavaliadas")
        finally:
            db.close()

    def job_alerts():
        db = SessionLocal()
        try:
            n = run_license_alerts(db)
            print(f"[scheduler] {n} alerta(s) enviado(s)")
        finally:
            db.close()

    scheduler.add_job(job_refresh, "interval", hours=1, id="refresh_licenses")
    scheduler.add_job(job_alerts, "cron", hour=8, minute=0, id="license_alerts")
    scheduler.start()


@app.on_event("shutdown")
def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


# --- Página pública ---

@app.get("/", response_class=HTMLResponse)
def public_landing(request: Request, user=Depends(optional_user)):
    return templates.TemplateResponse(
        "public/index.html",
        {"request": request, "user": user, "public_url": settings.public_base_url},
    )


@app.get("/suporte", response_class=HTMLResponse)
def public_support(request: Request):
    return templates.TemplateResponse("public/suporte.html", {"request": request})


# --- Admin ---

@app.get("/app/login", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user=Depends(optional_user)):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/app/login")
@app.post("/login")
def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(Operator).filter(Operator.username == username.strip()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuário ou senha inválidos."},
            status_code=401,
        )
    token = create_access_token(user.username)
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        "session_token",
        token,
        httponly=True,
        max_age=settings.access_token_ttl_minutes * 60,
        samesite="lax",
        secure=_cookie_secure(),
    )
    log_action(db, user.username, "login", "Login no gerenciador de licenças")
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("session_token")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), user: Operator = Depends(get_current_user)):
    stats = build_dashboard_stats(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "connections": test_connections(),
            "stats": stats,
            "products": PRODUCT_LABELS,
            "periods": PERIOD_LABELS,
            "payment_plans": PAYMENT_PLAN_LABELS,
        },
    )


@app.get("/clients", response_class=HTMLResponse)
def clients_page(request: Request, db: Session = Depends(get_db), user: Operator = Depends(get_current_user)):
    clients = db.query(Client).order_by(Client.nome.asc()).all()
    parent_options = db.query(Client).filter(Client.parent_client_id.is_(None)).order_by(Client.nome).all()
    client_rows = []
    for c in clients:
        licenses = db.query(LicenseRecord).filter(LicenseRecord.client_id == c.id).all()
        client_rows.append({"client": c, "summary": summarize_client_licenses(licenses)})
    return templates.TemplateResponse(
        "clients.html",
        {
            "request": request,
            "user": user,
            "client_rows": client_rows,
            "parent_options": parent_options,
            "products": PRODUCT_LABELS,
            "periods": PERIOD_LABELS,
        },
    )


@app.post("/clients")
def clients_create(
    nome: str = Form(...),
    razao_social: str = Form(""),
    document_type: str = Form("cnpj"),
    cnpj: str = Form(""),
    cpf: str = Form(""),
    email: str = Form(""),
    email_02: str = Form(""),
    telefone: str = Form(""),
    telefone_02: str = Form(""),
    telefone_03: str = Form(""),
    clinica_id_erp: str = Form(""),
    clinica_id_lab: str = Form(""),
    parent_client_id: str = Form(""),
    logradouro: str = Form(""),
    numero: str = Form(""),
    complemento: str = Form(""),
    bairro: str = Form(""),
    cidade: str = Form(""),
    uf: str = Form(""),
    cep: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    doc_value = cpf if document_type == "cpf" else cnpj
    if doc_value and not validate_document(document_type, doc_value):
        raise HTTPException(422, "Documento inválido")

    cid_erp = int(clinica_id_erp) if clinica_id_erp.strip().isdigit() else None
    cid_lab = int(clinica_id_lab) if clinica_id_lab.strip().isdigit() else None
    parent_id = int(parent_client_id) if parent_client_id.strip().isdigit() else None

    create_client(
        db,
        operator=user.username,
        nome=nome,
        razao_social=razao_social,
        document_type=document_type,
        cnpj=cnpj,
        cpf=cpf,
        email=email,
        email_02=email_02,
        telefone=telefone,
        telefone_02=telefone_02,
        telefone_03=telefone_03,
        clinica_id_erp=cid_erp,
        clinica_id_lab=cid_lab,
        parent_client_id=parent_id,
        notes=notes,
        address={
            "logradouro": logradouro,
            "numero": numero,
            "complemento": complemento,
            "bairro": bairro,
            "cidade": cidade,
            "uf": uf,
            "cep": cep,
        },
    )
    return RedirectResponse("/clients", status_code=303)


@app.get("/clients/{client_id}", response_class=HTMLResponse)
def client_detail(
    client_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(404, "Cliente não encontrado")
    licenses = (
        db.query(LicenseRecord)
        .filter(LicenseRecord.client_id == client_id)
        .order_by(LicenseRecord.id.desc())
        .all()
    )
    enriched = [{"license": lic, "effective": effective_for_license(lic)} for lic in licenses]
    parent = None
    if client.parent_client_id:
        parent = db.query(Client).filter(Client.id == client.parent_client_id).first()

    return templates.TemplateResponse(
        "client_detail.html",
        {
            "request": request,
            "user": user,
            "client": client,
            "parent": parent,
            "licenses": enriched,
            "products": PRODUCT_LABELS,
            "periods": PERIOD_LABELS,
            "payment_plans": PAYMENT_PLAN_LABELS,
            "block_days": settings.block_after_days,
            "cancel_days": settings.cancel_after_days,
            "stripe_enabled": stripe_enabled(),
        },
    )


@app.post("/clients/{client_id}/licenses")
def client_issue_license(
    client_id: int,
    produto: str = Form(...),
    periodo: str = Form(...),
    payment_plan: str = Form("annual"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    try:
        issue_license(
            db,
            operator=user.username,
            client_id=client_id,
            produto=produto,
            periodo=periodo,
            payment_plan=payment_plan,
            notes=notes,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return RedirectResponse(f"/clients/{client_id}", status_code=303)


@app.post("/licenses/{license_id}/renew")
def license_renew_action(
    license_id: int,
    periodo: str = Form(...),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    lic = db.query(LicenseRecord).filter(LicenseRecord.id == license_id).first()
    if not lic:
        raise HTTPException(404)
    try:
        renew_license(db, operator=user.username, license_id=license_id, periodo=periodo)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return RedirectResponse(f"/clients/{lic.client_id}", status_code=303)


@app.post("/licenses/{license_id}/revoke")
def license_revoke_action(
    license_id: int,
    reason: str = Form("Revogação administrativa"),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    lic = db.query(LicenseRecord).filter(LicenseRecord.id == license_id).first()
    if not lic:
        raise HTTPException(404)
    try:
        revoke_license(db, operator=user.username, license_id=license_id, reason=reason)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return RedirectResponse(f"/clients/{lic.client_id}", status_code=303)


@app.post("/licenses/{license_id}/payment-link")
def license_payment_link(
    license_id: int,
    payment_plan: str = Form("annual"),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    if not stripe_enabled():
        raise HTTPException(503, "Stripe não configurado")

    lic = db.query(LicenseRecord).filter(LicenseRecord.id == license_id).first()
    if not lic:
        raise HTTPException(404)
    client = db.query(Client).filter(Client.id == lic.client_id).first()
    if not client:
        raise HTTPException(404)

    base = settings.public_base_url or f"http://127.0.0.1:{settings.license_server_port}"
    session = create_checkout_session(
        client_id=client.id,
        license_id=lic.id,
        payment_plan=payment_plan,
        customer_email=client.email,
        success_url=f"{base}/clients/{client.id}?payment=success",
        cancel_url=f"{base}/clients/{client.id}?payment=cancelled",
    )

    db.add(
        Payment(
            client_id=client.id,
            license_id=lic.id,
            stripe_session_id=session["session_id"],
            payment_plan=payment_plan,
            status="pending",
        )
    )
    db.commit()
    log_action(db, user.username, "payment_link", f"Stripe session {session['session_id']}")
    return RedirectResponse(session["url"], status_code=303)


@app.post("/clients/{client_id}/cancel")
def client_cancel_action(
    client_id: int,
    reason: str = Form("Inadimplência"),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    try:
        cancel_client(db, operator=user.username, client_id=client_id, reason=reason)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return RedirectResponse("/clients", status_code=303)


@app.post("/admin/sync-all")
def sync_all(db: Session = Depends(get_db), user: Operator = Depends(get_current_user)):
    n = refresh_all_licenses(db)
    log_action(db, user.username, "sync_all", f"{n} licenças sincronizadas")
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/admin/users", response_class=HTMLResponse)
def admin_users_page(request: Request, db: Session = Depends(get_db), user: Operator = Depends(get_current_user)):
    operators = db.query(Operator).order_by(Operator.username.asc()).all()
    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "user": user, "operators": operators, "error": None},
    )


@app.post("/admin/users")
def admin_users_create(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    nome: str = Form(""),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    uname = username.strip().lower()
    if db.query(Operator).filter(Operator.username == uname).first():
        operators = db.query(Operator).order_by(Operator.username.asc()).all()
        return templates.TemplateResponse(
            "admin_users.html",
            {
                "request": request,
                "user": user,
                "operators": operators,
                "error": f"Usuário «{uname}» já existe.",
            },
            status_code=422,
        )
    db.add(
        Operator(
            username=uname,
            password_hash=hash_password(password),
            nome=nome.strip() or uname,
            ativo=True,
        )
    )
    db.commit()
    log_action(db, user.username, "operator_create", f"Operador {uname}")
    return RedirectResponse("/admin/users", status_code=303)


@app.post("/admin/users/{operator_id}/password")
def admin_users_password(
    operator_id: int,
    password: str = Form(...),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    op = db.query(Operator).filter(Operator.id == operator_id).first()
    if not op:
        raise HTTPException(404)
    op.password_hash = hash_password(password)
    db.commit()
    log_action(db, user.username, "operator_password", f"Senha alterada: {op.username}")
    return RedirectResponse("/admin/users", status_code=303)


@app.post("/admin/users/{operator_id}/toggle")
def admin_users_toggle(
    operator_id: int,
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    op = db.query(Operator).filter(Operator.id == operator_id).first()
    if not op:
        raise HTTPException(404)
    if op.username == user.username:
        raise HTTPException(422, "Não é possível desativar o próprio usuário.")
    op.ativo = not op.ativo
    db.commit()
    log_action(db, user.username, "operator_toggle", f"{op.username} ativo={op.ativo}")
    return RedirectResponse("/admin/users", status_code=303)


# --- APIs auxiliares (admin) ---

@app.get("/api/cep/{cep}")
def api_cep(cep: str, user: Operator = Depends(get_current_user)):
    data = fetch_address_by_cep(cep)
    if not data:
        raise HTTPException(404, "CEP não encontrado")
    return data


@app.get("/api/cnpj/{cnpj}")
def api_cnpj(cnpj: str, user: Operator = Depends(get_current_user)):
    data = fetch_cnpj_receita(cnpj)
    if not data:
        raise HTTPException(404, "CNPJ não encontrado ou inválido")
    return data


# --- Stripe webhook ---

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not stripe_enabled():
        raise HTTPException(503, "Stripe não configurado")

    from app.infra.stripe_payments import construct_webhook_event
    from app.licensing import STATUS_ACTIVE, now_utc

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = construct_webhook_event(payload, sig)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        payment = (
            db.query(Payment)
            .filter(Payment.stripe_session_id == session["id"])
            .first()
        )
        if payment:
            payment.status = "completed"
            payment.completed_at = now_utc()
            payment.stripe_payment_intent_id = session.get("payment_intent")
            lic = db.query(LicenseRecord).filter(LicenseRecord.id == payment.license_id).first()
            if lic:
                lic.payment_status = STATUS_ACTIVE
                lic.payment_plan = payment.payment_plan
            db.commit()

    return {"received": True}


def main():
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.license_server_host,
        port=settings.license_server_port,
        reload=os.getenv("LICENSE_SERVER_RELOAD", "").lower() in {"1", "true", "yes"},
        proxy_headers=settings.trust_proxy,
        forwarded_allow_ips="*" if settings.trust_proxy else None,
    )


if __name__ == "__main__":
    main()
