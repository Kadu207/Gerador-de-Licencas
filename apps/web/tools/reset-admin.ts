/**
 * Sincroniza operador admin com ADMIN_USERNAME / ADMIN_PASSWORD do .env.
 * Uso: npx tsx tools/reset-admin.ts
 */
import { config as loadEnv } from "dotenv";

loadEnv({ path: ".env", override: true });

import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const username = process.env.ADMIN_USERNAME ?? "admin";
  const password = process.env.ADMIN_PASSWORD ?? "";
  if (!password) throw new Error("ADMIN_PASSWORD nao definido em apps/web/.env");

  const passwordHash = await bcrypt.hash(password, 12);
  const existing = await prisma.operator.findUnique({ where: { username } });

  if (existing) {
    await prisma.operator.update({
      where: { username },
      data: { passwordHash, ativo: true, nome: existing.nome || "Administrador" },
    });
    console.log(`Senha do operador '${username}' atualizada a partir do .env.`);
  } else {
    await prisma.operator.create({
      data: { username, passwordHash, nome: "Administrador" },
    });
    console.log(`Operador '${username}' criado a partir do .env.`);
  }

  const ok = await bcrypt.compare(password, passwordHash);
  console.log("Verificacao:", ok ? "OK" : "FALHA");
  console.log(`Usuario: ${username}`);
  console.log(`Senha: ${password}`);
}

main()
  .catch((e) => {
    console.error("ERRO:", e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
