#!/usr/bin/env bash
# Sincroniza login admin do Gerador com o .env (útil se a senha do .env foi alterada após o 1º boot)
set -euo pipefail
cd /opt/gerador-licencas
echo "Usuário configurado:"
docker compose exec -T license-server python - <<'PY'
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
    print("Senha = valor de ADMIN_PASSWORD no .env de /opt/gerador-licencas")
finally:
    db.close()
PY
