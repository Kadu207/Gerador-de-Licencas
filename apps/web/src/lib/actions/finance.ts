"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { requireMasterOrRedirect } from "@/lib/auth";
import {
  cancelPaymentRecord,
  completePaymentRecord,
  updatePlanPrice,
} from "@/lib/services/finance-service";

export async function updatePlanPriceAction(formData: FormData) {
  const operator = await requireMasterOrRedirect();
  const planId = Number(formData.get("plan_id"));
  const price = Number(formData.get("price"));
  if (!planId || Number.isNaN(price) || price < 0) redirect("/finance?error=preco");

  await updatePlanPrice(planId, price, operator.username);
  revalidatePath("/finance");
  revalidatePath("/catalog");
  redirect("/finance?updated=plan");
}

export async function completePaymentAction(formData: FormData) {
  const operator = await requireMasterOrRedirect();
  const paymentId = Number(formData.get("payment_id"));
  if (!paymentId) redirect("/finance?error=pagamento");

  try {
    await completePaymentRecord(paymentId, operator.username);
  } catch {
    redirect("/finance?error=pagamento");
  }
  revalidatePath("/finance");
  redirect("/finance?updated=payment");
}

export async function cancelPaymentAction(formData: FormData) {
  const operator = await requireMasterOrRedirect();
  const paymentId = Number(formData.get("payment_id"));
  if (!paymentId) redirect("/finance?error=pagamento");

  try {
    await cancelPaymentRecord(paymentId, operator.username);
  } catch {
    redirect("/finance?error=pagamento");
  }
  revalidatePath("/finance");
  redirect("/finance?updated=payment");
}
