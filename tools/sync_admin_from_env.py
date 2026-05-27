#!/usr/bin/env python3
"""Sincroniza operador admin com ADMIN_USERNAME / ADMIN_PASSWORD do .env."""
from app.auth import hash_password
from app.config import settings
from app.models import Operator, SessionLocal, init_db

init_db()
db = SessionLocal()
try:
    username = settings.admin_username.strip()
    op = db.query(Operator).filter(Operator.username == username).first()
    if not op:
        op = Operator(
            username=username,
            password_hash=hash_password(settings.admin_password),
            nome="Administrador",
        )
        db.add(op)
        action = "criado"
    else:
        op.password_hash = hash_password(settings.admin_password)
        action = "atualizado"
    db.commit()
    print(f"Operador {action}: {username}")
    print("Use a senha definida em ADMIN_PASSWORD no arquivo .env deste projeto.")
finally:
    db.close()
