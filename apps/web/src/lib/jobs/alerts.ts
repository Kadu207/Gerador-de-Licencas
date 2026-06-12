import { prisma } from "@/lib/prisma";
import { ALERT_MILESTONES } from "@/domain/licensing";
import { effectiveForLicense } from "@/lib/services/license-service";

export async function runLicenseAlerts() {
  const licenses = await prisma.licenseRecord.findMany({
    where: { manualStatus: { notIn: ["revoked", "cancelled"] } },
    include: { client: true },
  });

  let sent = 0;
  for (const lic of licenses) {
    const eff = effectiveForLicense(lic);
    const days = eff.daysRemaining;
    if (!(ALERT_MILESTONES as readonly number[]).includes(days)) continue;

    const exists = await prisma.licenseAlertLog.findFirst({
      where: { licenseId: lic.id, milestoneDays: days },
    });
    if (exists) continue;

    const title = `Licença vence em ${days} dia(s)`;
    const message = `Cliente ${lic.client.nome} — produto ${lic.produto} — chave ****${lic.licenseKey.slice(-4)}`;

    await prisma.notification.create({
      data: { title, message, level: days <= 3 ? "critical" : "warning", licenseId: lic.id, clientId: lic.clientId },
    });
    await prisma.licenseAlertLog.create({
      data: { licenseId: lic.id, milestoneDays: days, channel: "in_app" },
    });
    sent++;
  }
  return sent;
}
