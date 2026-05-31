from __future__ import annotations

import json
import os
from decimal import Decimal, InvalidOperation
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
from app.infra.stripe_payments import PLAN_AMOUNTS, create_checkout_session, stripe_enabled
from app.infra.viacep import fetch_address_by_cep
from app.jobs.alerts import run_license_alerts
from app.dashboard_stats import build_dashboard_stats
from app.catalog import (
    BILLING_LABELS,
    STATUS_LABELS as CATALOG_STATUS_LABELS,
    create_software_product,
    licensable_products,
    parse_contracted_products,
    product_labels_dict,
    resolve_catalog_plan,
    seed_software_catalog,
    selectable_product_slugs,
    selectable_products,
    serialize_contracted_products,
    stripe_price_map,
    sync_product_labels_from_catalog,
)
from app.licensing import PAYMENT_PLAN_ANNUAL, PAYMENT_PLAN_LABELS, PERIOD_LABELS, PRODUCT_LABELS, STATUS_CANCELLED
from app.models import Client, LicenseRecord, Notification, Operator, Payment, SessionLocal, SoftwarePlan, SoftwareProduct, init_db
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
    update_client,
    update_client_contracted_systems,
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
        seed_software_catalog(db)
        sync_product_labels_from_catalog(db)
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
def public_landing(request: Request, db: Session = Depends(get_db), user=Depends(optional_user)):
    catalog = (
        db.query(SoftwareProduct)
        .order_by(SoftwareProduct.sort_order.asc(), SoftwareProduct.name.asc())
        .all()
    )
    return templates.TemplateResponse(
        "public/index.html",
        {
            "request": request,
            "user": user,
            "public_url": settings.public_base_url,
            "catalog": catalog,
            "status_labels": CATALOG_STATUS_LABELS,
            "billing_labels": BILLING_LABELS,
        },
    )


@app.get("/suporte", response_class=HTMLResponse)
def public_support(request: Request, user=Depends(optional_user)):
    return templates.TemplateResponse(
        "public/suporte.html",
        {"request": request, "user": user, "public_url": settings.public_base_url},
    )


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
    labels = product_labels_dict(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "connections": test_connections(),
            "stats": stats,
            "products": labels,
            "periods": PERIOD_LABELS,
            "payment_plans": PAYMENT_PLAN_LABELS,
        },
    )


@app.get("/clients", response_class=HTMLResponse)
def clients_page(request: Request, db: Session = Depends(get_db), user: Operator = Depends(get_current_user)):
    labels = product_labels_dict(db)
    clients = db.query(Client).order_by(Client.nome.asc()).all()
    parent_options = db.query(Client).filter(Client.parent_client_id.is_(None)).order_by(Client.nome).all()
    client_rows = []
    for c in clients:
        licenses = db.query(LicenseRecord).filter(LicenseRecord.client_id == c.id).all()
        contracted = parse_contracted_products(c.contracted_products)
        client_rows.append(
            {
                "client": c,
                "summary": summarize_client_licenses(
                    licenses, contracted_slugs=contracted, labels=labels
                ),
            }
        )
    return templates.TemplateResponse(
        "clients.html",
        {
            "request": request,
            "user": user,
            "client_rows": client_rows,
            "parent_options": parent_options,
            "system_options": selectable_products(db),
            "products": labels,
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
    contracted_systems: list[str] = Form(default=[]),
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
        contracted_products=serialize_contracted_products(contracted_systems),
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

    parent_options = (
        db.query(Client)
        .filter(Client.parent_client_id.is_(None), Client.id != client_id)
        .order_by(Client.nome)
        .all()
    )
    addr = client.address

    labels = product_labels_dict(db)
    contracted = parse_contracted_products(client.contracted_products)

    return templates.TemplateResponse(
        "client_detail.html",
        {
            "request": request,
            "user": user,
            "client": client,
            "parent": parent,
            "parent_options": parent_options,
            "address": addr,
            "licenses": enriched,
            "contracted_systems": contracted,
            "contracted_labels": [labels.get(s, s) for s in contracted],
            "system_options": selectable_products(db),
            "status_labels": CATALOG_STATUS_LABELS,
            "products": labels,
            "licensable_systems": licensable_products(db),
            "periods": PERIOD_LABELS,
            "payment_plans": PAYMENT_PLAN_LABELS,
            "block_days": settings.block_after_days,
            "cancel_days": settings.cancel_after_days,
            "stripe_enabled": stripe_enabled(),
            "stripe_prices": stripe_price_map(db),
            "saved": request.query_params.get("saved"),
            "payment_flash": request.query_params.get("payment"),
        },
    )


@app.post("/clients/{client_id}/contracted-systems")
def client_update_contracted_systems(
    client_id: int,
    contracted_systems: list[str] = Form(default=[]),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    try:
        update_client_contracted_systems(
            db,
            operator=user.username,
            client_id=client_id,
            slugs=contracted_systems,
            allowed_slugs=selectable_product_slugs(db),
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return RedirectResponse(f"/clients/{client_id}?saved=contracted", status_code=303)


@app.post("/clients/{client_id}/update")
def client_update(
    client_id: int,
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
    if parent_id == client_id:
        parent_id = None

    try:
        update_client(
            db,
            operator=user.username,
            client_id=client_id,
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
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return RedirectResponse(f"/clients/{client_id}?saved=profile", status_code=303)


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

    resolved = resolve_catalog_plan(db, lic.produto, payment_plan)
    if resolved:
        amount, product_name, plan_label = resolved
    else:
        labels = product_labels_dict(db)
        amount = PLAN_AMOUNTS.get(payment_plan, PLAN_AMOUNTS[PAYMENT_PLAN_ANNUAL])
        product_name = labels.get(lic.produto, lic.produto)
        plan_label = PAYMENT_PLAN_LABELS.get(payment_plan, payment_plan)

    base = settings.public_base_url or f"http://127.0.0.1:{settings.license_server_port}"
    session = create_checkout_session(
        client_id=client.id,
        license_id=lic.id,
        payment_plan=payment_plan,
        customer_email=client.email,
        success_url=f"{base}/clients/{client.id}?payment=success",
        cancel_url=f"{base}/clients/{client.id}?payment=cancelled",
        amount=amount,
        product_name=product_name,
        plan_label=plan_label,
    )

    db.add(
        Payment(
            client_id=client.id,
            license_id=lic.id,
            stripe_session_id=session["session_id"],
            payment_plan=payment_plan,
            amount=session.get("amount", amount),
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


@app.get("/systems", response_class=HTMLResponse)
def systems_portfolio(request: Request, db: Session = Depends(get_db), user: Operator = Depends(get_current_user)):
    products = (
        db.query(SoftwareProduct)
        .order_by(SoftwareProduct.sort_order.asc(), SoftwareProduct.name.asc())
        .all()
    )
    return templates.TemplateResponse(
        "systems.html",
        {
            "request": request,
            "user": user,
            "products": products,
            "status_labels": CATALOG_STATUS_LABELS,
            "billing_labels": BILLING_LABELS,
            "saved": request.query_params.get("saved"),
        },
    )


@app.post("/systems/products")
def systems_create_product(
    slug: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    status: str = Form("active"),
    license_enabled: str = Form("1"),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    try:
        create_software_product(
            db,
            slug=slug,
            name=name,
            description=description,
            status=status,
            license_enabled=license_enabled == "1",
        )
    except ValueError as exc:
        code = str(exc)
        if code == "SLUG_DUPLICADO":
            raise HTTPException(422, "Já existe um sistema com este identificador (slug).") from exc
        raise HTTPException(422, "Identificador inválido. Use letras minúsculas, números e _ (ex: meu_sistema).") from exc
    log_action(db, user.username, "system_create", f"Catálogo {slug}")
    return RedirectResponse("/systems?saved=1", status_code=303)


@app.post("/systems/products/{product_id}/update")
def systems_update_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    status: str = Form("active"),
    license_enabled: str = Form("1"),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    product = db.query(SoftwareProduct).filter(SoftwareProduct.id == product_id).first()
    if not product:
        raise HTTPException(404, "Sistema não encontrado")
    product.name = name.strip()
    product.description = description.strip()
    product.license_enabled = license_enabled == "1"
    if status in CATALOG_STATUS_LABELS:
        product.status = status
    db.commit()
    sync_product_labels_from_catalog(db)
    log_action(db, user.username, "system_update", f"Catálogo {product.slug}")
    return RedirectResponse("/systems?saved=1", status_code=303)


@app.post("/systems/products/{product_id}/plans")
def systems_add_plan(
    product_id: int,
    name: str = Form(...),
    billing_period: str = Form("annual"),
    price: str = Form("0"),
    description: str = Form(""),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    product = db.query(SoftwareProduct).filter(SoftwareProduct.id == product_id).first()
    if not product:
        raise HTTPException(404, "Sistema não encontrado")
    try:
        amount = Decimal(price.replace(",", "."))
    except InvalidOperation as exc:
        raise HTTPException(422, "Preço inválido") from exc
    max_order = max((p.sort_order for p in product.plans), default=0)
    db.add(
        SoftwarePlan(
            product_id=product.id,
            name=name.strip(),
            billing_period=billing_period,
            price=amount,
            description=description.strip(),
            sort_order=max_order + 10,
            active=True,
        )
    )
    db.commit()
    log_action(db, user.username, "plan_create", f"{product.slug} — {name.strip()}")
    return RedirectResponse("/systems?saved=1", status_code=303)


@app.post("/systems/plans/{plan_id}/update")
def systems_update_plan(
    plan_id: int,
    name: str = Form(...),
    billing_period: str = Form("annual"),
    price: str = Form("0"),
    description: str = Form(""),
    active: str = Form("1"),
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    plan = db.query(SoftwarePlan).filter(SoftwarePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plano não encontrado")
    try:
        amount = Decimal(price.replace(",", "."))
    except InvalidOperation as exc:
        raise HTTPException(422, "Preço inválido") from exc
    plan.name = name.strip()
    plan.billing_period = billing_period
    plan.price = amount
    plan.description = description.strip()
    plan.active = active == "1"
    db.commit()
    log_action(db, user.username, "plan_update", f"Plano {plan_id}")
    return RedirectResponse("/systems?saved=1", status_code=303)


@app.post("/systems/plans/{plan_id}/delete")
def systems_delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user: Operator = Depends(get_current_user),
):
    plan = db.query(SoftwarePlan).filter(SoftwarePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plano não encontrado")
    db.delete(plan)
    db.commit()
    log_action(db, user.username, "plan_delete", f"Plano {plan_id}")
    return RedirectResponse("/systems?saved=1", status_code=303)


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
