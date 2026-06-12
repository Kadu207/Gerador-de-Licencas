/**
 * Smoke test local: operador, cliente, emissão de licença, API validate.
 * Uso: npx tsx tools/smoke-local.ts
 */
import { config as loadEnv } from "dotenv";

loadEnv({ path: ".env", override: true });

import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";
import {
  generateLicenseKey,
  computeEndsAt,
  isValidLicenseKeyFormat,
  nowUtc,
  PRODUCT_CLOUD,
  PERIOD_TRIAL,
} from "../src/domain/licensing";

const prisma = new PrismaClient();
const BASE = process.env.PUBLIC_BASE_URL ?? "http://127.0.0.1:3000";
const API_KEY = process.env.PRODUCT_API_KEY ?? "";

async function main() {
  console.log("1. Health...");
  const health = await fetch(`${BASE}/api/health`);
  if (!health.ok) throw new Error(`Health falhou: ${health.status}`);
  console.log("   OK", await health.json());

  const adminUser = process.env.ADMIN_USERNAME ?? "admin";
  const adminPass = process.env.ADMIN_PASSWORD ?? "";
  if (!adminPass) throw new Error("ADMIN_PASSWORD não definido em .env");

  console.log("2. Operador admin...");
  let op = await prisma.operator.findUnique({ where: { username: adminUser } });
  if (!op) {
    op = await prisma.operator.create({
      data: {
        username: adminUser,
        passwordHash: await bcrypt.hash(adminPass, 12),
        nome: "Administrador",
      },
    });
    console.log("   Operador criado");
  } else {
    console.log("   Operador já existe");
  }

  console.log("3. Login API...");
  const loginRes = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: adminUser, password: adminPass }),
  });
  if (!loginRes.ok) throw new Error(`Login falhou: ${loginRes.status} ${await loginRes.text()}`);
  console.log("   Login OK");

  console.log("4. Cliente + licença...");
  const stamp = Date.now();
  const client = await prisma.client.create({
    data: {
      nome: `Smoke Test ${stamp}`,
      email: `smoke${stamp}@test.local`,
      documentType: "cnpj",
      cnpj: "52998224725",
      address: { create: { cidade: "São Paulo", uf: "SP", cep: "01310100" } },
    },
  });

  const start = nowUtc();
  const ends = computeEndsAt(start, PERIOD_TRIAL);
  const key = generateLicenseKey();
  if (!isValidLicenseKeyFormat(key)) throw new Error("Chave inválida");

  const lic = await prisma.licenseRecord.create({
    data: {
      clientId: client.id,
      licenseKey: key,
      produto: PRODUCT_CLOUD,
      periodo: PERIOD_TRIAL,
      paymentPlan: "annual",
      paymentStatus: "active",
      startsAt: start,
      endsAt: ends,
      paymentDueAt: ends,
      manualStatus: "active",
      createdBy: adminUser,
    },
  });
  console.log(`   Licença: ${lic.licenseKey} (${lic.produto}, ${lic.periodo})`);

  if (!API_KEY || API_KEY.includes("troque")) {
    console.log("5. API validate — pulado (PRODUCT_API_KEY não configurada)");
  } else {
    console.log("5. API validate...");
    const valRes = await fetch(`${BASE}/api/v1/licenses/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-License-Api-Key": API_KEY },
      body: JSON.stringify({ license_key: key, clinica_id: 1, product: "cloud" }),
    });
    const body = await valRes.json();
    if (!valRes.ok) throw new Error(`Validate falhou: ${JSON.stringify(body)}`);
    console.log("   valid:", body.valid, "| daysRemaining:", body.daysRemaining);
  }

  console.log("\n✓ Smoke test concluído com sucesso.");
  console.log(`  Painel: ${BASE}/clients/${client.id}`);
}

main()
  .catch((e) => {
    console.error("FALHA:", e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
