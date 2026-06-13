#!/usr/bin/env bash
# Cria/atualiza operadores master no Postgres (VPS ou local com Docker).
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$APP_DIR"

bash "$APP_DIR/infra/ops/provision-web-env.sh"

echo "==> Schema operators.role"
docker compose exec -T license-web node ./node_modules/prisma/build/index.js db push

echo "==> Seed operadores master"
docker compose exec -T license-web node <<'NODE'
const bcrypt = require("bcryptjs");
const { PrismaClient } = require("@prisma/client");

const operators = [
  {
    username: "supervisor",
    password: "GeneratorLic#super2026!",
    nome: "Supervisor Master",
    role: "master",
  },
  {
    username: "licencasadmin",
    password: "GeneratorLic#admin2026!",
    nome: "Admin Master Licencas",
    role: "master",
  },
];

(async () => {
  const prisma = new PrismaClient();
  try {
    for (const op of operators) {
      const passwordHash = await bcrypt.hash(op.password, 12);
      await prisma.operator.upsert({
        where: { username: op.username },
        create: {
          username: op.username,
          passwordHash,
          nome: op.nome,
          role: op.role,
          ativo: true,
        },
        update: {
          passwordHash,
          nome: op.nome,
          role: op.role,
          ativo: true,
        },
      });
      console.log(`OK: ${op.username} (${op.role})`);
    }
  } finally {
    await prisma.$disconnect();
  }
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
NODE

echo "==> Operadores master aplicados"
