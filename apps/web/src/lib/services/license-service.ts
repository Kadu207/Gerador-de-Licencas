import type { LicenseRecord, Client } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import { config } from "@/lib/config";
import {
  ALLOWED_PERIODS,
  PAYMENT_PLAN_ANNUAL,
  PERIOD_LABELS,
  PRODUCT_LABELS,
  PRODUCT_LAB,
  STATUS_ACTIVE,
  STATUS_CANCELLED,
  STATUS_REVOKED,
  computeEffectiveStatus,
  computeEndsAt,
  generateLabSecret,
  generateLicenseKey,
  nowUtc,
} from "@/domain/licensing";

export function effectiveForLicense(lic: LicenseRecord) {
  return computeEffectiveStatus({
    manualStatus: lic.manualStatus,
    endsAt: lic.endsAt,
    paymentDueAt: lic.paymentDueAt,
    blockAfterDays: config.blockAfterDays,
    cancelAfterDays: config.cancelAfterDays,
  });
}

export function licenseStatusPayload(lic: LicenseRecord, client: Client | null, effective: ReturnType<typeof effectiveForLicense>) {
  const valid =
    effective.validForSoftware && lic.manualStatus !== STATUS_REVOKED && lic.manualStatus !== STATUS_CANCELLED;
  return {
    valid,
    hasLicense: valid,
    status: effective.status,
    phase: effective.phase,
    produto: lic.produto,
    produtoLabel: PRODUCT_LABELS[lic.produto] ?? lic.produto,
    periodo: lic.periodo,
    periodoLabel: PERIOD_LABELS[lic.periodo] ?? lic.periodo,
    paymentPlan: lic.paymentPlan,
    startsAt: lic.startsAt?.toISOString() ?? null,
    endsAt: lic.endsAt?.toISOString() ?? null,
    paymentDueAt: lic.paymentDueAt?.toISOString() ?? null,
    daysRemaining: effective.daysRemaining,
    daysOverdue: effective.daysOverdue,
    licenseExpired: effective.licenseExpired,
    paymentPhase: effective.paymentPhase,
    licenseKeyMasked: lic.licenseKey.length >= 4 ? `****${lic.licenseKey.slice(-4)}` : "****",
    clinicaId: client?.clinicaIdLab ?? null,
    clinicaIdErp: client?.clinicaIdErp ?? null,
    unidadeId: lic.unidadeId,
    clienteNome: client?.nome ?? "",
    message: effective.message,
    alertLevel: effective.alertLevel,
    remainingLabel: effective.remainingLabel,
    source: "license-server",
  };
}

async function isLicensableProduct(slug: string): Promise<boolean> {
  const row = await prisma.softwareProduct.findFirst({
    where: { slug, licenseEnabled: true },
  });
  return row !== null;
}

export async function issueLicense(params: {
  operator: string;
  clientId: number;
  produto: string;
  periodo: string;
  paymentPlan?: string;
  notes?: string;
}) {
  if (!(await isLicensableProduct(params.produto))) throw new Error("INVALID_PRODUCT");
  if (!ALLOWED_PERIODS.has(params.periodo)) throw new Error("INVALID_PERIOD");

  const client = await prisma.client.findUnique({ where: { id: params.clientId } });
  if (!client) throw new Error("CLIENT_NOT_FOUND");

  const start = nowUtc();
  const ends = computeEndsAt(start, params.periodo);

  for (let i = 0; i < 12; i++) {
    const key = generateLicenseKey();
    const exists = await prisma.licenseRecord.findUnique({ where: { licenseKey: key } });
    if (exists) continue;

    const lic = await prisma.licenseRecord.create({
      data: {
        clientId: client.id,
        licenseKey: key,
        produto: params.produto,
        periodo: params.periodo,
        paymentPlan: params.paymentPlan ?? PAYMENT_PLAN_ANNUAL,
        paymentStatus: STATUS_ACTIVE,
        startsAt: start,
        endsAt: ends,
        paymentDueAt: ends,
        manualStatus: STATUS_ACTIVE,
        labSecret: params.produto === PRODUCT_LAB ? generateLabSecret() : null,
        createdBy: params.operator,
        notes: params.notes?.trim() ?? "",
      },
    });

    await prisma.auditLog.create({
      data: {
        operator: params.operator,
        action: "license_issue",
        detail: `${key} — ${params.produto}/${params.periodo} — cliente ${client.nome}`,
      },
    });

    return lic;
  }
  throw new Error("LICENSE_KEY_COLLISION");
}

export async function renewLicense(params: { operator: string; licenseId: number; periodo: string }) {
  if (!ALLOWED_PERIODS.has(params.periodo)) throw new Error("INVALID_PERIOD");

  const lic = await prisma.licenseRecord.findUnique({ where: { id: params.licenseId } });
  if (!lic) throw new Error("LICENSE_NOT_FOUND");

  const ref = nowUtc();
  const currentEnd = lic.endsAt && lic.endsAt > ref ? lic.endsAt : ref;
  const newEnd = computeEndsAt(currentEnd, params.periodo);

  const updated = await prisma.licenseRecord.update({
    where: { id: lic.id },
    data: {
      periodo: params.periodo,
      startsAt: currentEnd,
      endsAt: newEnd,
      paymentDueAt: newEnd,
      manualStatus: STATUS_ACTIVE,
      paymentStatus: STATUS_ACTIVE,
      labSecret: lic.produto === PRODUCT_LAB && !lic.labSecret ? generateLabSecret() : lic.labSecret,
    },
  });

  await prisma.auditLog.create({
    data: { operator: params.operator, action: "license_renew", detail: `${lic.licenseKey} renovada — ${params.periodo}` },
  });

  return updated;
}

export async function revokeLicense(params: { operator: string; licenseId: number; reason?: string }) {
  const lic = await prisma.licenseRecord.findUnique({ where: { id: params.licenseId } });
  if (!lic) throw new Error("LICENSE_NOT_FOUND");

  const updated = await prisma.licenseRecord.update({
    where: { id: lic.id },
    data: {
      manualStatus: STATUS_REVOKED,
      paymentStatus: STATUS_REVOKED,
      revokedAt: nowUtc(),
      revokedBy: params.operator,
      notes: params.reason ? `${lic.notes ?? ""} | revoke: ${params.reason}`.trim() : lic.notes,
    },
  });

  await prisma.auditLog.create({
    data: { operator: params.operator, action: "license_revoke", detail: `${lic.licenseKey} — ${params.reason ?? ""}` },
  });

  return updated;
}

export async function findLicenseByKey(key: string) {
  const lic = await prisma.licenseRecord.findUnique({ where: { licenseKey: key } });
  if (!lic) return { lic: null, client: null };
  const client = await prisma.client.findUnique({ where: { id: lic.clientId } });
  return { lic, client };
}

const PAYMENT_PLAN_RENEWAL_DAYS: Record<string, number> = {
  monthly: 30,
  semiannual: 183,
  annual: 365,
};

/** Estende validade técnica e cobrança após pagamento confirmado. */
export async function extendLicenseAfterPayment(params: {
  licenseId: number;
  paymentPlan: string;
  operator: string;
}) {
  const lic = await prisma.licenseRecord.findUnique({ where: { id: params.licenseId } });
  if (!lic) return null;

  const days = PAYMENT_PLAN_RENEWAL_DAYS[params.paymentPlan] ?? 365;
  const ref = nowUtc();
  const currentEnd = lic.endsAt && lic.endsAt > ref ? lic.endsAt : ref;
  const newEnd = new Date(currentEnd.getTime() + days * 24 * 60 * 60 * 1000);

  const updated = await prisma.licenseRecord.update({
    where: { id: lic.id },
    data: {
      endsAt: newEnd,
      paymentDueAt: newEnd,
      paymentPlan: params.paymentPlan,
      manualStatus: STATUS_ACTIVE,
      paymentStatus: STATUS_ACTIVE,
    },
  });

  await prisma.auditLog.create({
    data: {
      operator: params.operator,
      action: "license_payment_renew",
      detail: `${lic.licenseKey} +${days}d (${params.paymentPlan})`,
    },
  });

  return updated;
}
