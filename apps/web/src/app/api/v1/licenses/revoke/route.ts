import { NextRequest } from "next/server";
import { verifyProductApiKey } from "@/lib/api-auth";
import { isValidLicenseKeyFormat, normalizeLicenseKey } from "@/domain/licensing";
import { effectiveForLicense, findLicenseByKey, licenseStatusPayload, revokeLicense } from "@/lib/services/license-service";

export async function POST(req: NextRequest) {
  if (!verifyProductApiKey(req.headers.get("x-license-api-key"))) {
    return Response.json({ detail: "Chave de API inválida" }, { status: 401 });
  }

  const body = await req.json();
  const key = normalizeLicenseKey(body.license_key);
  if (!isValidLicenseKeyFormat(key)) {
    return Response.json({ detail: "INVALID_LICENSE_KEY" }, { status: 422 });
  }

  const { lic, client } = await findLicenseByKey(key);
  if (!lic) return Response.json({ detail: "LICENSE_NOT_FOUND" }, { status: 404 });

  const updated = await revokeLicense({ operator: "api_v1", licenseId: lic.id, reason: body.reason ?? "" });
  const effective = effectiveForLicense(updated);
  return Response.json({ msg: "OK", licenca: licenseStatusPayload(updated, client, effective) });
}
