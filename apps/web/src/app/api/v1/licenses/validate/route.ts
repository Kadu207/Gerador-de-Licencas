import { NextRequest } from "next/server";
import { verifyProductApiKey } from "@/lib/api-auth";
import {
  isValidLicenseKeyFormat,
  normalizeApiProduct,
  normalizeLicenseKey,
  productMatchesLicense,
} from "@/domain/licensing";
import { effectiveForLicense, findLicenseByKey, licenseStatusPayload } from "@/lib/services/license-service";

export async function POST(req: NextRequest) {
  if (!verifyProductApiKey(req.headers.get("x-license-api-key"))) {
    return Response.json({ detail: "Chave de API inválida" }, { status: 401 });
  }

  const body = await req.json();
  const key = normalizeLicenseKey(body.license_key);
  if (!isValidLicenseKeyFormat(key)) {
    return Response.json({ detail: "INVALID_LICENSE_KEY" }, { status: 422 });
  }

  const product = normalizeApiProduct(body.product ?? "lab");
  const { lic, client } = await findLicenseByKey(key);
  if (!lic) return Response.json({ detail: "LICENSE_NOT_FOUND" }, { status: 404 });
  if (!productMatchesLicense(product, lic.produto)) {
    return Response.json({ detail: "LICENSE_PRODUCT_MISMATCH" }, { status: 422 });
  }

  const boundClinica = client?.clinicaIdLab;
  if (boundClinica && boundClinica !== Number(body.clinica_id)) {
    return Response.json({ detail: "LICENSE_SCOPE_MISMATCH" }, { status: 409 });
  }

  const effective = effectiveForLicense(lic);
  return Response.json(licenseStatusPayload(lic, client, effective));
}
