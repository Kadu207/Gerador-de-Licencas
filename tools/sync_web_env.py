"""Sincroniza apps/web/.env a partir do .env raiz e app.config."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings as root_settings  # noqa: E402


def read_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def main() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    root = read_env(root_dir / ".env")
    example_path = root_dir / "apps/web/.env.example"
    web_path = root_dir / "apps/web/.env"
    base = (
        example_path.read_text(encoding="utf-8")
        if example_path.exists()
        else web_path.read_text(encoding="utf-8")
    )
    db_url = root_settings.local_database_url.replace(
        "postgresql+psycopg://", "postgresql://"
    )
    out: list[str] = []
    for line in base.splitlines():
        if line.startswith("DATABASE_URL="):
            out.append("DATABASE_URL=" + db_url)
        elif line.startswith("SECRET_KEY=") and root.get("SECRET_KEY"):
            out.append("SECRET_KEY=" + root["SECRET_KEY"])
        elif line.startswith("ADMIN_PASSWORD=") and root.get("ADMIN_PASSWORD"):
            out.append("ADMIN_PASSWORD=" + root["ADMIN_PASSWORD"])
        elif line.startswith("PRODUCT_API_KEY=") and root.get("PRODUCT_API_KEY"):
            out.append("PRODUCT_API_KEY=" + root["PRODUCT_API_KEY"])
        else:
            out.append(line)
    web_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("sync-web-env: apps/web/.env OK")


if __name__ == "__main__":
    main()
