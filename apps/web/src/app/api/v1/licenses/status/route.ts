import { NextRequest } from "next/server";
import { prisma } from "@/lib/prisma";
import { verifyProductApiKey } from "@/lib/api-auth";
import { normalizeLicenseKey } from "@/domain/licensing";
import { effectiveForLicense, findLicenseByKey, licenseStatusPayload } from "@/lib/services/license-service";
import { clinicaWhereClause } from "@/lib/services/license-scope";

export async function GET(req: NextRequest) {
  if (!verifyProductApiKey(req.headers.get("x-license-api-key"))) {
    return Response.json({ detail: "Chave de API inválida" }, { status: 401 });
  }

  const { searchParams } = req.nextUrl;
  const licenseKey = searchParams.get("license_key");

  if (licenseKey) {
    const key = normalizeLicenseKey(licenseKey);
    const { lic, client } = await findLicenseByKey(key);
    if (!lic) return Response.json({ detail: "LICENSE_NOT_FOUND" }, { status: 404 });
    const effective = effectiveForLicense(lic);
    return Response.json(licenseStatusPayload(lic, client, effective));
  }

  const clinicaId = Number(searchParams.get("clinica_id"));
  const unidadeId = searchParams.get("unidade_id");
  const product = searchParams.get("product") ?? "lab";

  if (!clinicaId || Number.isNaN(clinicaId)) {
    return Response.json({ detail: "clinica_id obrigatório" }, { status: 422 });
  }

  const lic = await prisma.licenseRecord.findFirst({
    where: {
      ...clinicaWhereClause(product, clinicaId),
      ...(unidadeId ? { unidadeId } : { OR: [{ unidadeId: null }, { unidadeId: "" }] }),
    },
    orderBy: { id: "desc" },
    include: { client: true },
  });

  if (!lic) {
    return Response.json({
      valid: false,
      hasLicense: false,
      status: "none",
      clinicaId,
      unidadeId,
      source: "license-server",
      message: "Nenhuma licença vinculada a esta unidade.",
    });
  }

  const effective = effectiveForLicense(lic);
  return Response.json(licenseStatusPayload(lic, lic.client, effective));
}
