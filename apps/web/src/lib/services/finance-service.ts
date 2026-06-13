import Stripe from "stripe";
import { prisma } from "@/lib/prisma";
import { config } from "@/lib/config";
import { resolveCatalogPlan, listCatalog } from "@/lib/services/catalog-service";
import { extendLicenseAfterPayment } from "@/lib/services/license-service";
import { STATUS_ACTIVE, nowUtc } from "@/domain/licensing";

function stripeClient() {
  if (!config.stripeSecretKey) return null;
  return new Stripe(config.stripeSecretKey);
}

export function stripeConfigured(): boolean {
  return Boolean(config.stripeSecretKey?.trim() && config.stripeWebhookSecret?.trim());
}

export async function getFinanceDashboard() {
  const [payments, pending, completed, products, catalog, atRisk] = await Promise.all([
    prisma.payment.findMany({
      orderBy: { createdAt: "desc" },
      take: 100,
      include: { client: true, license: true },
    }),
    prisma.payment.count({ where: { status: "pending" } }),
    prisma.payment.aggregate({ where: { status: "completed" }, _sum: { amount: true } }),
    prisma.softwareProduct.count({ where: { licenseEnabled: true } }),
    listCatalog(),
    prisma.licenseRecord.findMany({
      where: {
        manualStatus: STATUS_ACTIVE,
        OR: [{ paymentStatus: "grace" }, { paymentStatus: "blocked" }, { paymentStatus: "pending" }],
      },
      take: 20,
      include: { client: true },
      orderBy: { paymentDueAt: "asc" },
    }),
  ]);

  const revenueByProduct: Record<string, number> = {};
  for (const p of payments) {
    if (p.status !== "completed" || !p.license) continue;
    const slug = p.license.produto;
    revenueByProduct[slug] = (revenueByProduct[slug] ?? 0) + Number(p.amount);
  }

  const completedThisMonth = payments.filter((p) => {
    if (p.status !== "completed" || !p.completedAt) return false;
    const now = new Date();
    return (
      p.completedAt.getMonth() === now.getMonth() && p.completedAt.getFullYear() === now.getFullYear()
    );
  });

  const monthRevenue = completedThisMonth.reduce((sum, p) => sum + Number(p.amount), 0);

  return {
    payments,
    pendingCount: pending,
    totalRevenue: Number(completed._sum.amount ?? 0),
    monthRevenue,
    activeProducts: products,
    catalog,
    revenueByProduct,
    atRiskLicenses: atRisk,
    stripeReady: stripeConfigured(),
  };
}

/** @deprecated use getFinanceDashboard */
export async function getFinanceSummary() {
  const d = await getFinanceDashboard();
  return {
    payments: d.payments.slice(0, 50),
    pendingCount: d.pendingCount,
    totalRevenue: d.totalRevenue,
    activeProducts: d.activeProducts,
  };
}

export async function createCheckoutSession(params: {
  clientId: number;
  licenseId?: number;
  productSlug: string;
  paymentPlan: string;
  operator: string;
}) {
  const stripe = stripeClient();
  if (!stripe) throw new Error("STRIPE_NOT_CONFIGURED");

  const client = await prisma.client.findUnique({ where: { id: params.clientId } });
  if (!client) throw new Error("CLIENT_NOT_FOUND");

  const plan = await resolveCatalogPlan(params.productSlug, params.paymentPlan);
  if (!plan) throw new Error("PLAN_NOT_FOUND");

  const amountCents = Math.round(plan.amount * 100);

  const payment = await prisma.payment.create({
    data: {
      clientId: client.id,
      licenseId: params.licenseId ?? null,
      amount: plan.amount,
      paymentPlan: params.paymentPlan,
      status: "pending",
    },
  });

  const session = await stripe.checkout.sessions.create({
    mode: "payment",
    customer_email: client.email || undefined,
    line_items: [
      {
        price_data: {
          currency: "brl",
          unit_amount: amountCents,
          product_data: {
            name: `${plan.productName} — ${plan.planLabel}`,
            description: `Licenciamento InovatiTech — cliente ${client.nome}`,
          },
        },
        quantity: 1,
      },
    ],
    success_url: `${config.publicBaseUrl}/finance?paid=1&session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${config.publicBaseUrl}/clients/${client.id}?cancelled=1`,
    metadata: {
      payment_id: String(payment.id),
      client_id: String(client.id),
      license_id: params.licenseId ? String(params.licenseId) : "",
      operator: params.operator,
      product_slug: params.productSlug,
      payment_plan: params.paymentPlan,
    },
  });

  await prisma.payment.update({
    where: { id: payment.id },
    data: { stripeSessionId: session.id },
  });

  await prisma.auditLog.create({
    data: {
      operator: params.operator,
      action: "stripe_checkout",
      detail: `Sessão ${session.id} — ${client.nome} — R$ ${plan.amount}`,
    },
  });

  return { url: session.url, paymentId: payment.id };
}

export async function completePaymentRecord(paymentId: number, operator: string) {
  const payment = await prisma.payment.findUnique({ where: { id: paymentId } });
  if (!payment) throw new Error("PAYMENT_NOT_FOUND");
  if (payment.status === "completed") return payment;

  await prisma.payment.update({
    where: { id: paymentId },
    data: { status: "completed", completedAt: nowUtc() },
  });

  if (payment.licenseId) {
    await extendLicenseAfterPayment({
      licenseId: payment.licenseId,
      paymentPlan: payment.paymentPlan,
      operator,
    });
  }

  await prisma.auditLog.create({
    data: { operator, action: "payment_manual_complete", detail: `Pagamento #${paymentId}` },
  });

  return prisma.payment.findUnique({ where: { id: paymentId } });
}

export async function cancelPaymentRecord(paymentId: number, operator: string) {
  const payment = await prisma.payment.findUnique({ where: { id: paymentId } });
  if (!payment) throw new Error("PAYMENT_NOT_FOUND");
  if (payment.status !== "pending") throw new Error("PAYMENT_NOT_PENDING");

  await prisma.payment.update({ where: { id: paymentId }, data: { status: "cancelled" } });
  await prisma.auditLog.create({
    data: { operator, action: "payment_cancel", detail: `Pagamento #${paymentId} cancelado` },
  });
}

export async function updatePlanPrice(planId: number, price: number, operator: string) {
  const plan = await prisma.softwarePlan.update({
    where: { id: planId },
    data: { price },
    include: { product: true },
  });
  await prisma.auditLog.create({
    data: {
      operator,
      action: "catalog_price_update",
      detail: `${plan.product.slug}/${plan.billingPeriod} → R$ ${price}`,
    },
  });
  return plan;
}

export async function handleStripeWebhook(rawBody: string, signature: string) {
  const stripe = stripeClient();
  if (!stripe || !config.stripeWebhookSecret) throw new Error("STRIPE_NOT_CONFIGURED");

  const event = stripe.webhooks.constructEvent(rawBody, signature, config.stripeWebhookSecret);

  if (event.type === "checkout.session.completed") {
    const session = event.data.object as Stripe.Checkout.Session;
    const paymentId = Number(session.metadata?.payment_id ?? 0);
    if (!paymentId) return;

    const operator = session.metadata?.operator ?? "stripe_webhook";

    await prisma.payment.update({
      where: { id: paymentId },
      data: {
        status: "completed",
        completedAt: nowUtc(),
        stripePaymentIntentId: typeof session.payment_intent === "string" ? session.payment_intent : null,
        paymentMethod: session.payment_method_types?.[0] ?? "card",
      },
    });

    const payment = await prisma.payment.findUnique({ where: { id: paymentId } });
    if (payment?.licenseId) {
      await extendLicenseAfterPayment({
        licenseId: payment.licenseId,
        paymentPlan: payment.paymentPlan,
        operator,
      });
    }
  }
}
