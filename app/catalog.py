"""Catálogo de sistemas Inova TI — portfólio, labels e seed."""
from __future__ import annotations

import json
import re

from decimal import Decimal

from sqlalchemy.orm import Session

from app.licensing import (
    PRODUCT_CLOUD,
    PRODUCT_LAB,
    PRODUCT_LIMPEZA,
    PRODUCT_OUTROS,
    PRODUCT_VDE,
    PRODUCT_LABELS,
    PAYMENT_PLAN_ANNUAL,
    PAYMENT_PLAN_MONTHLY,
    PAYMENT_PLAN_SEMIANNUAL,
)
from app.models import SoftwarePlan, SoftwareProduct

STATUS_ACTIVE = "active"
STATUS_CONSTRUCTION = "construction"
STATUS_PLANNED = "planned"

STATUS_LABELS = {
    STATUS_ACTIVE: "Disponível",
    STATUS_CONSTRUCTION: "Em construção",
    STATUS_PLANNED: "Em breve",
}

BILLING_LABELS = {
    "monthly": "Mensal",
    "semiannual": "Semestral",
    "annual": "Anual",
    "triennial": "Trienal",
    "onetime": "Pagamento único",
    "custom": "Sob consulta",
}

# payment_plan (licença/Stripe) → billing_period (catálogo)
PAYMENT_PLAN_TO_BILLING: dict[str, str] = {
    PAYMENT_PLAN_MONTHLY: "monthly",
    PAYMENT_PLAN_SEMIANNUAL: "semiannual",
    PAYMENT_PLAN_ANNUAL: "annual",
}

DEFAULT_CATALOG: list[dict] = [
    {
        "slug": PRODUCT_CLOUD,
        "name": "Excellence Dental Cloud",
        "description": (
            "ERP em nuvem para clínicas odontológicas: agenda, financeiro, estoque, "
            "prontuário e integração com laboratório protético."
        ),
        "status": STATUS_ACTIVE,
        "sort_order": 10,
        "license_enabled": True,
        "plans": [
            {"name": "Plano Mensal", "billing_period": "monthly", "price": 497.00, "description": "Por clínica / mês"},
            {"name": "Plano Semestral", "billing_period": "semiannual", "price": 2486.00, "description": "Economia de 1 mês"},
            {"name": "Plano Anual", "billing_period": "annual", "price": 4970.00, "description": "Economia de 2 meses"},
            {"name": "Plano Trienal", "billing_period": "triennial", "price": 0, "description": "Condições especiais — consulte comercial"},
        ],
    },
    {
        "slug": PRODUCT_LAB,
        "name": "Dental Lab",
        "description": (
            "Gestão completa para laboratório protético: ordens de serviço, produção, "
            "entregas, financeiro e portal para clínicas parceiras."
        ),
        "status": STATUS_ACTIVE,
        "sort_order": 20,
        "license_enabled": True,
        "plans": [
            {"name": "Plano Mensal", "billing_period": "monthly", "price": 299.00, "description": "Por laboratório / mês"},
            {"name": "Plano Semestral", "billing_period": "semiannual", "price": 1599.00, "description": "Economia de 2 meses"},
            {"name": "Plano Anual", "billing_period": "annual", "price": 2999.00, "description": "Economia de 2 meses"},
        ],
    },
    {
        "slug": PRODUCT_LIMPEZA,
        "name": "Script de Limpeza completo",
        "description": (
            "Automação de limpeza e manutenção de ambientes Windows/Linux em clínicas e "
            "escritórios — rotinas agendadas, logs e relatórios."
        ),
        "status": STATUS_ACTIVE,
        "sort_order": 30,
        "license_enabled": True,
        "plans": [
            {"name": "Licença anual", "billing_period": "annual", "price": 297.00, "description": "Por unidade / ano"},
            {"name": "Licença vitalícia", "billing_period": "onetime", "price": 890.00, "description": "Pagamento único"},
        ],
    },
    {
        "slug": PRODUCT_VDE,
        "name": "VDE Incorporadora",
        "description": (
            "Sistema e site para incorporadora imobiliária — em desenvolvimento. "
            "Gestão de empreendimentos, unidades, contratos e portal do cliente."
        ),
        "status": STATUS_CONSTRUCTION,
        "sort_order": 40,
        "license_enabled": True,
        "plans": [
            {"name": "Pré-lançamento", "billing_period": "custom", "price": 0, "description": "Valores a definir na go-live"},
        ],
    },
    {
        "slug": PRODUCT_OUTROS,
        "name": "Outros sistemas",
        "description": "Novos produtos Inova TI em roadmap — entre em contato para early access.",
        "status": STATUS_PLANNED,
        "sort_order": 50,
        "license_enabled": False,
        "plans": [],
    },
]


def parse_contracted_products(raw: str | None) -> list[str]:
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data if x]
    except json.JSONDecodeError:
        pass
    return [p.strip() for p in raw.split(",") if p.strip()]


def serialize_contracted_products(slugs: list[str]) -> str:
    clean = sorted({s.strip() for s in slugs if s and s.strip()})
    return json.dumps(clean)


def product_labels_dict(db: Session) -> dict[str, str]:
    labels = dict(PRODUCT_LABELS)
    for row in db.query(SoftwareProduct).order_by(SoftwareProduct.sort_order).all():
        labels[row.slug] = row.name
    return labels


def licensable_products(db: Session) -> list[SoftwareProduct]:
    return (
        db.query(SoftwareProduct)
        .filter(SoftwareProduct.license_enabled.is_(True))
        .order_by(SoftwareProduct.sort_order)
        .all()
    )


def selectable_products(db: Session) -> list[SoftwareProduct]:
    """Sistemas exibidos no cadastro/edição de cliente."""
    return (
        db.query(SoftwareProduct)
        .filter(
            SoftwareProduct.status.in_(
                [STATUS_ACTIVE, STATUS_CONSTRUCTION, STATUS_PLANNED]
            )
        )
        .order_by(SoftwareProduct.sort_order)
        .all()
    )


def selectable_product_slugs(db: Session) -> set[str]:
    return {p.slug for p in selectable_products(db)}


def normalize_product_slug(raw: str) -> str:
    s = raw.strip().lower().replace("-", "_").replace(" ", "_")
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s[:32]


def is_valid_product_slug(slug: str) -> bool:
    return bool(slug) and bool(re.match(r"^[a-z][a-z0-9_]{1,31}$", slug))


def is_licensable_product(db: Session, slug: str) -> bool:
    return (
        db.query(SoftwareProduct)
        .filter(
            SoftwareProduct.slug == slug,
            SoftwareProduct.license_enabled.is_(True),
        )
        .first()
        is not None
    )


def create_software_product(
    db: Session,
    *,
    slug: str,
    name: str,
    description: str = "",
    status: str = STATUS_ACTIVE,
    license_enabled: bool = True,
) -> SoftwareProduct:
    clean_slug = normalize_product_slug(slug)
    if not is_valid_product_slug(clean_slug):
        raise ValueError("SLUG_INVALIDO")
    if db.query(SoftwareProduct).filter(SoftwareProduct.slug == clean_slug).first():
        raise ValueError("SLUG_DUPLICADO")

    max_order = db.query(SoftwareProduct.sort_order).order_by(SoftwareProduct.sort_order.desc()).first()
    sort_order = (max_order[0] if max_order and max_order[0] else 0) + 10

    product = SoftwareProduct(
        slug=clean_slug,
        name=name.strip(),
        description=description.strip(),
        status=status if status in STATUS_LABELS else STATUS_ACTIVE,
        sort_order=sort_order,
        license_enabled=license_enabled,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    PRODUCT_LABELS[clean_slug] = product.name
    return product


STRIPE_BILLING_PERIODS = frozenset({"monthly", "semiannual", "annual"})

COMMERCIAL_PLAN_DEFAULTS: dict[str, list[tuple]] = {
    PRODUCT_CLOUD: [
        ("monthly", "Plano Mensal", 497.00, "Por clínica / mês", 10),
        ("semiannual", "Plano Semestral", 2486.00, "Economia de 1 mês", 15),
        ("annual", "Plano Anual", 4970.00, "Economia de 2 meses", 20),
    ],
    PRODUCT_LAB: [
        ("monthly", "Plano Mensal", 299.00, "Por laboratório / mês", 10),
        ("semiannual", "Plano Semestral", 1599.00, "Economia de 2 meses", 15),
        ("annual", "Plano Anual", 2999.00, "Economia de 2 meses", 20),
    ],
}


def commercial_plans_for_product(product: SoftwareProduct) -> list[SoftwarePlan]:
    return [
        p
        for p in product.plans
        if p.active and p.billing_period in STRIPE_BILLING_PERIODS and p.price and p.price > 0
    ]


def apply_commercial_plan_prices(db: Session, slugs: list[str] | None = None) -> int:
    """Aplica tabela comercial Cloud/Lab (ou slugs informados). Retorna planos atualizados."""
    targets = slugs or list(COMMERCIAL_PLAN_DEFAULTS.keys())
    updated = 0
    for slug in targets:
        plans_def = COMMERCIAL_PLAN_DEFAULTS.get(slug)
        if not plans_def:
            continue
        product = db.query(SoftwareProduct).filter(SoftwareProduct.slug == slug).first()
        if not product:
            continue
        for billing, name, price, description, sort_order in plans_def:
            row = (
                db.query(SoftwarePlan)
                .filter(
                    SoftwarePlan.product_id == product.id,
                    SoftwarePlan.billing_period == billing,
                )
                .first()
            )
            if row:
                row.name = name
                row.price = price
                row.description = description
                row.sort_order = sort_order
                row.active = True
            else:
                db.add(
                    SoftwarePlan(
                        product_id=product.id,
                        name=name,
                        billing_period=billing,
                        price=price,
                        description=description,
                        sort_order=sort_order,
                        active=True,
                    )
                )
            updated += 1
    db.commit()
    return updated


def format_product_list(slugs: list[str], labels: dict[str, str]) -> str:
    if not slugs:
        return "—"
    return ", ".join(labels.get(s, s) for s in slugs)


def resolve_catalog_plan(
    db: Session,
    product_slug: str,
    payment_plan: str,
) -> tuple[Decimal, str, str] | None:
    """Retorna (valor, nome produto, rótulo plano) para Checkout Stripe."""
    billing = PAYMENT_PLAN_TO_BILLING.get(payment_plan)
    if not billing:
        return None
    product = db.query(SoftwareProduct).filter(SoftwareProduct.slug == product_slug).first()
    if not product:
        return None
    plan = (
        db.query(SoftwarePlan)
        .filter(
            SoftwarePlan.product_id == product.id,
            SoftwarePlan.billing_period == billing,
            SoftwarePlan.active.is_(True),
        )
        .order_by(SoftwarePlan.sort_order)
        .first()
    )
    if not plan or plan.price is None or plan.price <= 0:
        return None
    label = BILLING_LABELS.get(billing, billing)
    return Decimal(str(plan.price)), product.name, f"{plan.name} ({label})"


def stripe_price_map(db: Session) -> dict[str, dict[str, float]]:
    """Mapa produto → payment_plan → preço (UI admin / Stripe)."""
    out: dict[str, dict[str, float]] = {}
    for product in db.query(SoftwareProduct).all():
        prices: dict[str, float] = {}
        for pay_plan, billing in PAYMENT_PLAN_TO_BILLING.items():
            plan = (
                db.query(SoftwarePlan)
                .filter(
                    SoftwarePlan.product_id == product.id,
                    SoftwarePlan.billing_period == billing,
                    SoftwarePlan.active.is_(True),
                )
                .first()
            )
            if plan and plan.price and plan.price > 0:
                prices[pay_plan] = float(plan.price)
        if prices:
            out[product.slug] = prices
    return out


def seed_software_catalog(db: Session) -> None:
    if db.query(SoftwareProduct).count() > 0:
        return
    for item in DEFAULT_CATALOG:
        product = SoftwareProduct(
            slug=item["slug"],
            name=item["name"],
            description=item["description"],
            status=item["status"],
            sort_order=item["sort_order"],
            license_enabled=item["license_enabled"],
        )
        db.add(product)
        db.flush()
        for i, plan in enumerate(item.get("plans", [])):
            db.add(
                SoftwarePlan(
                    product_id=product.id,
                    name=plan["name"],
                    billing_period=plan["billing_period"],
                    price=plan["price"],
                    description=plan.get("description", ""),
                    sort_order=(i + 1) * 10,
                    active=True,
                )
            )
    db.commit()


def sync_product_labels_from_catalog(db: Session) -> None:
    """Atualiza PRODUCT_LABELS em runtime a partir do catálogo (UI/API)."""
    for row in db.query(SoftwareProduct).all():
        PRODUCT_LABELS[row.slug] = row.name
