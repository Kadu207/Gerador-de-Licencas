import { NextRequest } from "next/server";
import { verifyProductApiKey } from "@/lib/api-auth";
import { isValidLicenseKeyFormat, normalizeLicenseKey } from "@/domain/licensing";
import { effectiveForLicense, findLicenseByKey, licenseStatusPayload } from "@/lib/services/license-service";

export async function GET(req: NextRequest) {
  if (!verifyProductApiKey(req.headers.get("x-license-api-key"))) {
    return Response.json({ detail: "Chave de API inválida" }, { status: 401 });
  }

  const key = normalizeLicenseKey(req.nextUrl.searchParams.get("license_key"));
  if (!isValidLicenseKeyFormat(key)) {
    return Response.json({ detail: "INVALID_LICENSE_KEY" }, { status: 422 });
  }

  const { lic, client } = await findLicenseByKey(key);
  if (!lic) return Response.json({ detail: "LICENSE_NOT_FOUND" }, { status: 404 });

  const effective = effectiveForLicense(lic);
  return Response.json({
    ok: true,
    ...licenseStatusPayload(lic, client, effective),
  });
}
