import { NextRequest } from "next/server";
import { handleStripeWebhook } from "@/lib/services/finance-service";

export async function POST(req: NextRequest) {
  const signature = req.headers.get("stripe-signature");
  if (!signature) return Response.json({ error: "missing signature" }, { status: 400 });
  const raw = await req.text();
  try {
    await handleStripeWebhook(raw, signature);
    return Response.json({ received: true });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "webhook error";
    return Response.json({ error: msg }, { status: 400 });
  }
}
