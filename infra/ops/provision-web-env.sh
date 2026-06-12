#!/usr/bin/env bash
# Gera apps/web/.env na VPS a partir do .env raiz (sem commitar segredos).
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$APP_DIR"

python3 <<'PY'
from pathlib import Path
from urllib.parse import quote_plus

def read_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data

root = Path(".env")
example = Path("apps/web/.env.example")
out = Path("apps/web/.env")
if not root.exists():
    raise SystemExit("ERRO: .env raiz ausente")
if not example.exists():
    raise SystemExit("ERRO: apps/web/.env.example ausente")

env = read_env(root)
password = env.get("POSTGRES_APP_PASSWORD", "")
if not password:
    raise SystemExit("ERRO: POSTGRES_APP_PASSWORD ausente no .env raiz")

db_url = f"postgresql://licencas:{quote_plus(password)}@license-db:5432/licencas_db"
lines: list[str] = []
for line in example.read_text(encoding="utf-8").splitlines():
    if line.startswith("DATABASE_URL="):
        lines.append("DATABASE_URL=" + db_url)
    elif line.startswith("SECRET_KEY=") and env.get("SECRET_KEY"):
        lines.append("SECRET_KEY=" + env["SECRET_KEY"])
    elif line.startswith("ADMIN_USERNAME=") and env.get("ADMIN_USERNAME"):
        lines.append("ADMIN_USERNAME=" + env["ADMIN_USERNAME"])
    elif line.startswith("ADMIN_PASSWORD=") and env.get("ADMIN_PASSWORD"):
        lines.append("ADMIN_PASSWORD=" + env["ADMIN_PASSWORD"])
    elif line.startswith("PRODUCT_API_KEY=") and env.get("PRODUCT_API_KEY"):
        lines.append("PRODUCT_API_KEY=" + env["PRODUCT_API_KEY"])
    elif line.startswith("PUBLIC_BASE_URL=") and env.get("PUBLIC_BASE_URL"):
        lines.append("PUBLIC_BASE_URL=" + env["PUBLIC_BASE_URL"])
    elif line.startswith("STRIPE_SECRET_KEY=") and env.get("STRIPE_SECRET_KEY"):
        lines.append("STRIPE_SECRET_KEY=" + env["STRIPE_SECRET_KEY"])
    elif line.startswith("STRIPE_WEBHOOK_SECRET=") and env.get("STRIPE_WEBHOOK_SECRET"):
        lines.append("STRIPE_WEBHOOK_SECRET=" + env["STRIPE_WEBHOOK_SECRET"])
    else:
        lines.append(line)

out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"provision-web-env: {out} OK")
PY
