import { NextRequest } from "next/server";
import { prisma } from "@/lib/prisma";
import { verifyProductApiKey } from "@/lib/api-auth";
import {
  STATUS_ACTIVE,
  STATUS_CANCELLED,
  STATUS_REVOKED,
  isValidLicenseKeyFormat,
  normalizeApiProduct,
  normalizeLicenseKey,
  productMatchesLicense,
} from "@/domain/licensing";
import { effectiveForLicense, findLicenseByKey, licenseStatusPayload } from "@/lib/services/license-service";
import { boundToOtherScope, clinicaBindingField } from "@/lib/services/license-scope";

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
  if (lic.manualStatus === STATUS_REVOKED || lic.manualStatus === STATUS_CANCELLED) {
    return Response.json({ detail: "LICENSE_REVOKED" }, { status: 422 });
  }

  const clinicaId = Number(body.clinica_id);
  if (boundToOtherScope(lic, client, clinicaId, body.unidade_id, product)) {
    return Response.json({ detail: "LICENSE_ALREADY_USED" }, { status: 409 });
  }

  const scopeUid = (body.unidade_id ?? "").trim() || null;
  await prisma.licenseRecord.update({
    where: { id: lic.id },
    data: {
      manualStatus: STATUS_ACTIVE,
      installationId: body.installation_id?.trim() || lic.installationId,
      unidadeId: lic.unidadeId || scopeUid,
    },
  });

  if (client) {
    const field = clinicaBindingField(product);
    if (!client[field]) {
      await prisma.client.update({
        where: { id: client.id },
        data: { [field]: clinicaId },
      });
    }
  }

  const updated = await prisma.licenseRecord.findUnique({ where: { id: lic.id } });
  const refreshedClient = await prisma.client.findUnique({ where: { id: lic.clientId } });
  const effective = effectiveForLicense(updated!);
  return Response.json({ msg: "OK", licenca: licenseStatusPayload(updated!, refreshedClient, effective) });
}
