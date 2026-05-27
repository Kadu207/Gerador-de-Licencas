"""Catálogo de sistemas Inova TI — portfólio, labels e seed."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.licensing import (
    PRODUCT_CLOUD,
    PRODUCT_LAB,
    PRODUCT_LIMPEZA,
    PRODUCT_OUTROS,
    PRODUCT_VDE,
    PRODUCT_LABELS,
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
            {"name": "Plano Mensal", "billing_period": "monthly", "price": 397.00, "description": "Por laboratório / mês"},
            {"name": "Plano Anual", "billing_period": "annual", "price": 3970.00, "description": "Economia de 2 meses"},
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


def format_product_list(slugs: list[str], labels: dict[str, str]) -> str:
    if not slugs:
        return "—"
    return ", ".join(labels.get(s, s) for s in slugs)


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
