/**
 * Cria/atualiza operadores master no Postgres.
 * Uso: npx tsx tools/seed-operators.ts
 */
import { config as loadEnv } from "dotenv";

loadEnv({ path: ".env", override: true });

import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

const OPERATORS = [
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
] as const;

async function upsertOperator(op: (typeof OPERATORS)[number]) {
  const passwordHash = await bcrypt.hash(op.password, 12);
  const existing = await prisma.operator.findUnique({ where: { username: op.username } });

  if (existing) {
    await prisma.operator.update({
      where: { username: op.username },
      data: { passwordHash, nome: op.nome, role: op.role, ativo: true },
    });
    console.log(`Atualizado: ${op.username} (${op.role})`);
  } else {
    await prisma.operator.create({
      data: {
        username: op.username,
        passwordHash,
        nome: op.nome,
        role: op.role,
      },
    });
    console.log(`Criado: ${op.username} (${op.role})`);
  }

  const ok = await bcrypt.compare(op.password, passwordHash);
  if (!ok) throw new Error(`Falha ao validar hash de ${op.username}`);
}

async function main() {
  for (const op of OPERATORS) {
    await upsertOperator(op);
  }
  console.log("Operadores master prontos.");
}

main()
  .catch((e) => {
    console.error("ERRO:", e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
