import { prisma } from "@/lib/prisma";
import {
  PRODUCT_CLOUD,
  PRODUCT_LAB,
  PRODUCT_LIMPEZA,
  PRODUCT_OUTROS,
  PRODUCT_VDE,
  PAYMENT_PLAN_ANNUAL,
  PAYMENT_PLAN_MONTHLY,
  PAYMENT_PLAN_SEMIANNUAL,
} from "@/domain/licensing";

const PAYMENT_PLAN_TO_BILLING: Record<string, string> = {
  [PAYMENT_PLAN_MONTHLY]: "monthly",
  [PAYMENT_PLAN_SEMIANNUAL]: "semiannual",
  [PAYMENT_PLAN_ANNUAL]: "annual",
};

const DEFAULT_CATALOG = [
  {
    slug: PRODUCT_CLOUD,
    name: "Excellence Dental Cloud",
    description: "ERP em nuvem para clínicas odontológicas.",
    status: "active",
    sortOrder: 10,
    licenseEnabled: true,
    plans: [
      { name: "Plano Mensal", billingPeriod: "monthly", price: 497, description: "Por clínica / mês", sortOrder: 10 },
      { name: "Plano Semestral", billingPeriod: "semiannual", price: 2486, description: "Economia de 1 mês", sortOrder: 15 },
      { name: "Plano Anual", billingPeriod: "annual", price: 4970, description: "Economia de 2 meses", sortOrder: 20 },
    ],
  },
  {
    slug: PRODUCT_LAB,
    name: "Dental Lab",
    description: "Gestão para laboratório protético.",
    status: "active",
    sortOrder: 20,
    licenseEnabled: true,
    plans: [
      { name: "Plano Mensal", billingPeriod: "monthly", price: 299, description: "Por laboratório / mês", sortOrder: 10 },
      { name: "Plano Semestral", billingPeriod: "semiannual", price: 1599, description: "Economia de 2 meses", sortOrder: 15 },
      { name: "Plano Anual", billingPeriod: "annual", price: 2999, description: "Economia de 2 meses", sortOrder: 20 },
    ],
  },
  {
    slug: PRODUCT_LIMPEZA,
    name: "Script de Limpeza completo",
    description: "Automação de limpeza e manutenção.",
    status: "active",
    sortOrder: 30,
    licenseEnabled: true,
    plans: [{ name: "Licença anual", billingPeriod: "annual", price: 297, description: "Por unidade / ano", sortOrder: 10 }],
  },
  {
    slug: PRODUCT_VDE,
    name: "VDE Incorporadora",
    description: "Sistema para incorporadora imobiliária — em desenvolvimento.",
    status: "construction",
    sortOrder: 40,
    licenseEnabled: true,
    plans: [{ name: "Pré-lançamento", billingPeriod: "custom", price: 0, description: "Valores na go-live", sortOrder: 10 }],
  },
  {
    slug: PRODUCT_OUTROS,
    name: "Outros sistemas",
    description: "Novos produtos Inova TI em roadmap.",
    status: "planned",
    sortOrder: 50,
    licenseEnabled: false,
    plans: [],
  },
];

export async function seedSoftwareCatalog() {
  const count = await prisma.softwareProduct.count();
  if (count > 0) return;

  for (const item of DEFAULT_CATALOG) {
    const product = await prisma.softwareProduct.create({
      data: {
        slug: item.slug,
        name: item.name,
        description: item.description,
        status: item.status,
        sortOrder: item.sortOrder,
        licenseEnabled: item.licenseEnabled,
      },
    });
    for (const plan of item.plans) {
      await prisma.softwarePlan.create({
        data: { productId: product.id, ...plan },
      });
    }
  }
}

export async function resolveCatalogPlan(productSlug: string, paymentPlan: string) {
  const billing = PAYMENT_PLAN_TO_BILLING[paymentPlan];
  if (!billing) return null;

  const product = await prisma.softwareProduct.findUnique({ where: { slug: productSlug } });
  if (!product) return null;

  const plan = await prisma.softwarePlan.findFirst({
    where: { productId: product.id, billingPeriod: billing, active: true, price: { gt: 0 } },
    orderBy: { sortOrder: "asc" },
  });
  if (!plan) return null;

  return { amount: Number(plan.price), productName: product.name, planLabel: plan.name };
}

export async function listCatalog() {
  return prisma.softwareProduct.findMany({
    include: { plans: { where: { active: true }, orderBy: { sortOrder: "asc" } } },
    orderBy: { sortOrder: "asc" },
  });
}
