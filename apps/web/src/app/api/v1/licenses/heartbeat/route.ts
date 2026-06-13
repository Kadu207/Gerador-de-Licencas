import { NextRequest } from "next/server";
import { verifyProductApiKey } from "@/lib/api-auth";
import { isValidLicenseKeyFormat, normalizeLicenseKey } from "@/domain/licensing";
import { effectiveForLicense, findLicenseByKey } from "@/lib/services/license-service";

export async function GET(req: NextRequest) {
  if (!verifyProductApiKey(req.headers.get("x-license-api-key"))) {
    return Response.json({ detail: "Chave de API inválida" }, { status: 401 });
  }

  const key = normalizeLicenseKey(req.nextUrl.searchParams.get("license_key"));
  if (!isValidLicenseKeyFormat(key)) {
    return Response.json({ detail: "INVALID_LICENSE_KEY" }, { status: 422 });
  }

  const { lic } = await findLicenseByKey(key);
  if (!lic) {
    return Response.json({ valid: false, blocked: true, reason: "LICENSE_NOT_FOUND" });
  }

  const effective = effectiveForLicense(lic);
  const valid = effective.validForSoftware;
  return Response.json({
    valid,
    blocked: !valid,
    licenseExpired: effective.licenseExpired,
    paymentPhase: effective.paymentPhase,
    daysRemaining: effective.daysRemaining,
    alertLevel: effective.alertLevel,
  });
}
