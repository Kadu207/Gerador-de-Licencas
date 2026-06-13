"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { prisma } from "@/lib/prisma";
import { requireOperator } from "@/lib/auth";
import { canCreateCheckout, canRevokeLicense } from "@/lib/roles";
import { issueLicense, renewLicense, revokeLicense } from "@/lib/services/license-service";
import { createCheckoutSession } from "@/lib/services/finance-service";
import { ensureBootstrap } from "@/lib/bootstrap";

export async function createClientAction(formData: FormData) {
  const operator = await requireOperator();
  if (!operator) redirect("/login");
  await ensureBootstrap();

  const client = await prisma.client.create({
    data: {
      nome: String(formData.get("nome") ?? "").trim(),
      razaoSocial: String(formData.get("razao_social") ?? "").trim(),
      documentType: String(formData.get("document_type") ?? "cnpj"),
      cnpj: String(formData.get("cnpj") ?? "").trim(),
      cpf: String(formData.get("cpf") ?? "").trim(),
      email: String(formData.get("email") ?? "").trim(),
      email02: String(formData.get("email_02") ?? "").trim(),
      telefone: String(formData.get("telefone") ?? "").trim(),
      telefone02: String(formData.get("telefone_02") ?? "").trim(),
      telefone03: String(formData.get("telefone_03") ?? "").trim(),
      clinicaIdErp: formData.get("clinica_id_erp") ? Number(formData.get("clinica_id_erp")) : null,
      clinicaIdLab: formData.get("clinica_id_lab") ? Number(formData.get("clinica_id_lab")) : null,
      parentClientId: formData.get("parent_client_id") ? Number(formData.get("parent_client_id")) : null,
      notes: String(formData.get("notes") ?? "").trim(),
      address: {
        create: {
          logradouro: String(formData.get("logradouro") ?? "").trim(),
          numero: String(formData.get("numero") ?? "").trim(),
          complemento: String(formData.get("complemento") ?? "").trim(),
          bairro: String(formData.get("bairro") ?? "").trim(),
          cidade: String(formData.get("cidade") ?? "").trim(),
          uf: String(formData.get("uf") ?? "").trim(),
          cep: String(formData.get("cep") ?? "").trim(),
        },
      },
    },
  });

  await prisma.auditLog.create({
    data: { operator: operator.username, action: "client_create", detail: `Cliente ${client.id} — ${client.nome}` },
  });

  revalidatePath("/clients");
  redirect(`/clients/${client.id}`);
}

export async function issueLicenseAction(formData: FormData) {
  const operator = await requireOperator();
  if (!operator) redirect("/login");

  const clientId = Number(formData.get("client_id"));
  await issueLicense({
    operator: operator.username,
    clientId,
    produto: String(formData.get("produto")),
    periodo: String(formData.get("periodo")),
    paymentPlan: String(formData.get("payment_plan") ?? "annual"),
    notes: String(formData.get("notes") ?? ""),
  });

  revalidatePath(`/clients/${clientId}`);
  redirect(`/clients/${clientId}`);
}

export async function renewLicenseAction(formData: FormData) {
  const operator = await requireOperator();
  if (!operator) redirect("/login");

  const licenseId = Number(formData.get("license_id"));
  const lic = await renewLicense({ operator: operator.username, licenseId, periodo: String(formData.get("periodo")) });
  revalidatePath(`/clients/${lic.clientId}`);
  redirect(`/clients/${lic.clientId}`);
}

export async function revokeLicenseAction(formData: FormData) {
  const operator = await requireOperator();
  if (!operator) redirect("/login");
  if (!canRevokeLicense(operator.role)) redirect("/dashboard?error=acesso");

  const licenseId = Number(formData.get("license_id"));
  const lic = await revokeLicense({
    operator: operator.username,
    licenseId,
    reason: String(formData.get("reason") ?? ""),
  });
  revalidatePath(`/clients/${lic.clientId}`);
  redirect(`/clients/${lic.clientId}`);
}

export async function checkoutAction(formData: FormData) {
  const operator = await requireOperator();
  if (!operator) redirect("/login");
  if (!canCreateCheckout(operator.role)) redirect("/dashboard?error=acesso");

  const result = await createCheckoutSession({
    operator: operator.username,
    clientId: Number(formData.get("client_id")),
    licenseId: formData.get("license_id") ? Number(formData.get("license_id")) : undefined,
    productSlug: String(formData.get("produto")),
    paymentPlan: String(formData.get("payment_plan")),
  });

  if (result.url) redirect(result.url);
  redirect("/finance");
}
