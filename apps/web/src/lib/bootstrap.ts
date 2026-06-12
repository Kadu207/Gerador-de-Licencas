import { prisma } from "@/lib/prisma";
import { config } from "@/lib/config";
import { hashPassword, verifyPassword } from "@/lib/auth";
import { seedSoftwareCatalog } from "@/lib/services/catalog-service";

let bootstrapped = false;

async function ensureAdminOperator() {
  if (!config.adminPassword) return;

  const passwordHash = await hashPassword(config.adminPassword);
  const existing = await prisma.operator.findUnique({
    where: { username: config.adminUsername },
  });

  if (!existing) {
    await prisma.operator.create({
      data: {
        username: config.adminUsername,
        passwordHash,
        nome: "Administrador",
      },
    });
    return;
  }

  const matches = await verifyPassword(config.adminPassword, existing.passwordHash);
  if (!matches) {
    await prisma.operator.update({
      where: { username: config.adminUsername },
      data: { passwordHash, ativo: true },
    });
  }
}

export async function ensureBootstrap() {
  if (bootstrapped) return;
  await seedSoftwareCatalog();
  await ensureAdminOperator();
  bootstrapped = true;
}
