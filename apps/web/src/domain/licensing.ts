/**
 * Regras de licenciamento — portadas do gerador Excellence Dental Cloud.
 */
import { randomBytes } from "crypto";

export const LICENSE_KEY_LEN = 25;
export const LICENSE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

export const PRODUCT_CLOUD = "cloud";
export const PRODUCT_LAB = "lab";
export const PRODUCT_VDE = "vde";
export const PRODUCT_LIMPEZA = "limpeza";
export const PRODUCT_OUTROS = "outros";

export const PERIOD_TRIAL = "trial";
export const PERIOD_1Y = "1y";
export const PERIOD_2Y = "2y";
export const PERIOD_3Y = "3y";
export const PERIOD_4Y = "4y";
export const PERIOD_5Y = "5y";

export const PAYMENT_PLAN_MONTHLY = "monthly";
export const PAYMENT_PLAN_SEMIANNUAL = "semiannual";
export const PAYMENT_PLAN_ANNUAL = "annual";

export const ALLOWED_PERIODS = new Set([
  PERIOD_TRIAL,
  PERIOD_1Y,
  PERIOD_2Y,
  PERIOD_3Y,
  PERIOD_4Y,
  PERIOD_5Y,
]);

export const ALLOWED_PAYMENT_PLANS = new Set([
  PAYMENT_PLAN_MONTHLY,
  PAYMENT_PLAN_SEMIANNUAL,
  PAYMENT_PLAN_ANNUAL,
]);

export const PERIOD_DAYS: Record<string, number> = {
  [PERIOD_TRIAL]: 30,
  [PERIOD_1Y]: 365,
  [PERIOD_2Y]: 730,
  [PERIOD_3Y]: 1095,
  [PERIOD_4Y]: 1460,
  [PERIOD_5Y]: 1825,
};

export const PRODUCT_LABELS: Record<string, string> = {
  [PRODUCT_CLOUD]: "Excellence Dental Cloud",
  [PRODUCT_LAB]: "Dental Lab",
  [PRODUCT_VDE]: "VDE Incorporadora",
  [PRODUCT_LIMPEZA]: "Script de Limpeza completo",
  [PRODUCT_OUTROS]: "Outros sistemas",
};

export const PERIOD_LABELS: Record<string, string> = {
  [PERIOD_TRIAL]: "Teste (30 dias)",
  [PERIOD_1Y]: "1 ano",
  [PERIOD_2Y]: "2 anos",
  [PERIOD_3Y]: "3 anos",
  [PERIOD_4Y]: "4 anos",
  [PERIOD_5Y]: "5 anos",
};

export const ALERT_MILESTONES = [20, 15, 7, 3, 2, 1] as const;

export const STATUS_PENDING = "pending";
export const STATUS_ACTIVE = "active";
export const STATUS_GRACE = "grace";
export const STATUS_BLOCKED = "blocked";
export const STATUS_CANCELLED = "cancelled";
export const STATUS_REVOKED = "revoked";
export const STATUS_EXPIRED = "expired";

const API_PRODUCT_ALIASES: Record<string, string> = {
  cloud: PRODUCT_CLOUD,
  erp: PRODUCT_CLOUD,
  excellence: PRODUCT_CLOUD,
  excellence_cloud: PRODUCT_CLOUD,
  lab: PRODUCT_LAB,
  dental_lab: PRODUCT_LAB,
  vde: PRODUCT_VDE,
  vde_incorporadora: PRODUCT_VDE,
  limpeza: PRODUCT_LIMPEZA,
  cleaning: PRODUCT_LIMPEZA,
  script_limpeza: PRODUCT_LIMPEZA,
};

export function nowUtc(): Date {
  return new Date();
}

export function generateLicenseKey(): string {
  const bytes = randomBytes(LICENSE_KEY_LEN);
  let key = "";
  for (let i = 0; i < LICENSE_KEY_LEN; i++) {
    key += LICENSE_ALPHABET[bytes[i]! % LICENSE_ALPHABET.length];
  }
  return key;
}

export function generateLabSecret(): string {
  return randomBytes(32).toString("hex");
}

export function normalizeLicenseKey(key: string | null | undefined): string {
  return (key ?? "").replace(/[^A-Za-z0-9]/g, "").toUpperCase().slice(0, LICENSE_KEY_LEN);
}

export function isValidLicenseKeyFormat(key: string): boolean {
  const normalized = normalizeLicenseKey(key);
  return new RegExp(`^[A-Z0-9]{${LICENSE_KEY_LEN}}$`).test(normalized);
}

export function computeEndsAt(start: Date, periodo: string): Date {
  const days = PERIOD_DAYS[periodo] ?? PERIOD_DAYS[PERIOD_TRIAL]!;
  const end = new Date(start);
  end.setUTCDate(end.getUTCDate() + days);
  return end;
}

export function normalizeApiProduct(product: string): string {
  const raw = (product ?? "").trim().toLowerCase();
  return API_PRODUCT_ALIASES[raw] ?? raw;
}

export function productMatchesLicense(apiProduct: string, licenseProduto: string): boolean {
  const normalized = normalizeApiProduct(apiProduct);
  const legacy = licenseProduto.trim().toLowerCase();
  if (legacy === "cloud_lab") return false;
  return normalized === legacy;
}

export function daysUntil(target: Date | null | undefined, ref: Date): number {
  if (!target) return 0;
  const t = Date.UTC(target.getUTCFullYear(), target.getUTCMonth(), target.getUTCDate());
  const r = Date.UTC(ref.getUTCFullYear(), ref.getUTCMonth(), ref.getUTCDate());
  return Math.max(0, Math.floor((t - r) / 86400000));
}

export type LicenseValidity = {
  licenseStatus: string;
  licenseExpired: boolean;
  daysRemaining: number;
  validForSoftware: boolean;
};

export function computeLicenseValidity(params: {
  manualStatus: string;
  endsAt: Date | string | null | undefined;
  now?: Date;
}): LicenseValidity {
  const ref = params.now ?? nowUtc();
  const { manualStatus, endsAt } = params;

  if (manualStatus === STATUS_CANCELLED || manualStatus === STATUS_REVOKED) {
    return { licenseStatus: manualStatus, licenseExpired: true, daysRemaining: 0, validForSoftware: false };
  }

  const due = parseTs(endsAt);
  if (!due) {
    return { licenseStatus: STATUS_PENDING, licenseExpired: false, daysRemaining: 0, validForSoftware: false };
  }

  const remaining = daysUntil(due, ref);
  const expired = ref > due;
  return {
    licenseStatus: expired ? STATUS_EXPIRED : STATUS_ACTIVE,
    licenseExpired: expired,
    daysRemaining: expired ? 0 : remaining,
    validForSoftware: !expired,
  };
}

export type PaymentPhase = {
  paymentPhase: string;
  paymentStatus: string;
  daysOverdue: number;
  blockAt: string | null;
  cancelEligibleAt: string | null;
  message: string;
};

export function computePaymentPhase(params: {
  manualStatus: string;
  paymentDueAt: Date | string | null | undefined;
  blockAfterDays: number;
  cancelAfterDays: number;
  now?: Date;
}): PaymentPhase {
  const ref = params.now ?? nowUtc();
  const { manualStatus, paymentDueAt, blockAfterDays, cancelAfterDays } = params;

  if (manualStatus === STATUS_CANCELLED || manualStatus === STATUS_REVOKED) {
    return {
      paymentPhase: manualStatus,
      paymentStatus: manualStatus,
      daysOverdue: 0,
      blockAt: null,
      cancelEligibleAt: null,
      message: "Cliente cancelado ou licença revogada.",
    };
  }

  const due = parseTs(paymentDueAt);
  if (!due) {
    return {
      paymentPhase: STATUS_PENDING,
      paymentStatus: STATUS_PENDING,
      daysOverdue: 0,
      blockAt: null,
      cancelEligibleAt: null,
      message: "Aguardando definição de pagamento.",
    };
  }

  const blockAt = new Date(due);
  blockAt.setUTCDate(blockAt.getUTCDate() + blockAfterDays);
  const cancelAt = new Date(due);
  cancelAt.setUTCDate(cancelAt.getUTCDate() + cancelAfterDays);
  const daysOverdue = Math.max(0, Math.floor((ref.getTime() - due.getTime()) / 86400000));

  if (ref <= due) {
    return {
      paymentPhase: STATUS_ACTIVE,
      paymentStatus: STATUS_ACTIVE,
      daysOverdue: 0,
      blockAt: blockAt.toISOString(),
      cancelEligibleAt: cancelAt.toISOString(),
      message: "Pagamento em dia.",
    };
  }

  if (ref <= blockAt) {
    const graceLeft = blockAfterDays - daysOverdue;
    return {
      paymentPhase: STATUS_GRACE,
      paymentStatus: STATUS_GRACE,
      daysOverdue,
      blockAt: blockAt.toISOString(),
      cancelEligibleAt: cancelAt.toISOString(),
      message: `Pagamento vencido há ${daysOverdue} dia(s). Carência comercial: ${graceLeft} dia(s) restante(s).`,
    };
  }

  if (ref <= cancelAt) {
    return {
      paymentPhase: STATUS_BLOCKED,
      paymentStatus: STATUS_BLOCKED,
      daysOverdue,
      blockAt: blockAt.toISOString(),
      cancelEligibleAt: cancelAt.toISOString(),
      message: `Bloqueio comercial por inadimplência (${daysOverdue} dias após vencimento do pagamento).`,
    };
  }

  return {
    paymentPhase: "cancel_eligible",
    paymentStatus: STATUS_BLOCKED,
    daysOverdue,
    blockAt: blockAt.toISOString(),
    cancelEligibleAt: cancelAt.toISOString(),
    message: `Elegível para cancelamento comercial (${daysOverdue} dias). Limite: ${cancelAfterDays} dias após vencimento do pagamento.`,
  };
}

export function computeAlertLevel(params: {
  licenseExpired: boolean;
  daysRemaining: number;
  paymentPhase: string;
}): string {
  if (params.licenseExpired) return "expired";
  if (params.paymentPhase === STATUS_BLOCKED || params.paymentPhase === "cancel_eligible") return "critical";
  if (params.paymentPhase === STATUS_GRACE) return "warning";
  if ((ALERT_MILESTONES as readonly number[]).includes(params.daysRemaining)) return "warning";
  if (params.daysRemaining <= 3) return "critical";
  return "none";
}

export type EffectiveStatus = LicenseValidity &
  PaymentPhase & {
    status: string;
    phase: string;
    validForSoftware: boolean;
    alertLevel: string;
    remainingLabel: string;
  };

export function computeEffectiveStatus(params: {
  manualStatus: string;
  endsAt: Date | string | null | undefined;
  paymentDueAt?: Date | string | null | undefined;
  blockAfterDays?: number;
  cancelAfterDays?: number;
  now?: Date;
}): EffectiveStatus {
  const ref = params.now ?? nowUtc();
  const blockAfterDays = params.blockAfterDays ?? 30;
  const cancelAfterDays = params.cancelAfterDays ?? 45;

  const validity = computeLicenseValidity({ manualStatus: params.manualStatus, endsAt: params.endsAt, now: ref });
  const payment = computePaymentPhase({
    manualStatus: params.manualStatus,
    paymentDueAt: params.paymentDueAt ?? params.endsAt,
    blockAfterDays,
    cancelAfterDays,
    now: ref,
  });

  let validForSoftware =
    validity.validForSoftware && params.manualStatus !== STATUS_REVOKED && params.manualStatus !== STATUS_CANCELLED;
  if (payment.paymentPhase === STATUS_BLOCKED || payment.paymentPhase === "cancel_eligible") {
    validForSoftware = false;
  }

  const alertLevel = computeAlertLevel({
    licenseExpired: validity.licenseExpired,
    daysRemaining: validity.daysRemaining,
    paymentPhase: payment.paymentPhase,
  });

  let status = payment.paymentPhase;
  if (validity.licenseExpired) status = STATUS_EXPIRED;

  return {
    ...validity,
    ...payment,
    status,
    phase: status,
    daysRemaining: validity.daysRemaining,
    daysOverdue: payment.daysOverdue,
    validForSoftware,
    alertLevel,
    remainingLabel: formatRemainingCounter(validity.daysRemaining),
  };
}

export function formatRemainingCounter(days: number): string {
  if (days <= 0) return "Vencido";
  const years = Math.floor(days / 365);
  const rem = days % 365;
  const months = Math.floor(rem / 30);
  const d = rem % 30;
  const parts: string[] = [];
  if (years) parts.push(`${years} ano${years > 1 ? "s" : ""}`);
  if (months) parts.push(`${months} mês${months > 1 ? "es" : ""}`);
  if (d || parts.length === 0) parts.push(`${d} dia${d !== 1 ? "s" : ""}`);
  return parts.join(", ");
}

function parseTs(value: Date | string | null | undefined): Date | null {
  if (value == null) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  const raw = String(value).trim().replace("T", " ").replace("Z", "");
  const parsed = new Date(raw.includes(" ") ? raw : `${raw}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}
