"""Extrai logo base64 do site inovatitech.com.br para static/."""
import base64
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = urllib.request.urlopen("https://inovatitech.com.br", timeout=30).read().decode("utf-8", errors="ignore")
match = re.search(
    r'class="logo"[^>]*>\s*<img[^>]+src="(data:image/[^;]+;base64,[^"]+)"',
    html,
)
if not match:
    raise SystemExit("Logo não encontrado no HTML")
header, b64 = match.group(1).split(",", 1)
ext = "jpg" if "jpeg" in header else "png"
out = ROOT / "static" / f"inova-ti-logo.{ext}"
out.write_bytes(base64.b64decode(b64))
print(f"OK {out} ({out.stat().st_size} bytes)")
