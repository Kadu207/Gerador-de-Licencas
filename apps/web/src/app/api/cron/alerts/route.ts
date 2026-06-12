import { NextRequest } from "next/server";
import { runLicenseAlerts } from "@/lib/jobs/alerts";

export async function POST(req: NextRequest) {
  const secret = process.env.CRON_SECRET ?? "";
  if (!secret || req.headers.get("x-cron-secret") !== secret) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  const sent = await runLicenseAlerts();
  return Response.json({ ok: true, notificationsSent: sent });
}
