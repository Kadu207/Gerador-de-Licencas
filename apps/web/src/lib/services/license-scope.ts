import type { Client, LicenseRecord } from "@prisma/client";
import { normalizeApiProduct, PRODUCT_CLOUD, PRODUCT_LAB, PRODUCT_VDE } from "@/domain/licensing";

/** Cloud e VDE vinculam `clinica_id` ao ERP; Lab vincula ao `clinica_id_lab`. */
export function usesErpClinicaId(apiProduct: string): boolean {
  const normalized = normalizeApiProduct(apiProduct);
  return normalized === PRODUCT_CLOUD || normalized === PRODUCT_VDE || normalized === "erp";
}

export function boundClinicaId(client: Client | null, apiProduct: string): number | null {
  if (!client) return null;
  return usesErpClinicaId(apiProduct) ? client.clinicaIdErp : client.clinicaIdLab;
}

export function boundToOtherScope(
  lic: LicenseRecord,
  client: Client | null,
  clinicaId: number,
  unidadeId: string | null | undefined,
  apiProduct: string,
): boolean {
  const bound = boundClinicaId(client, apiProduct);
  if (bound && bound !== clinicaId) return true;
  if (lic.unidadeId) {
    return lic.unidadeId !== (unidadeId ?? "").trim();
  }
  return false;
}

/** Campos do cliente a preencher na ativação (somente se ainda vazio). */
export function clinicaBindingField(apiProduct: string): "clinicaIdErp" | "clinicaIdLab" {
  return usesErpClinicaId(apiProduct) ? "clinicaIdErp" : "clinicaIdLab";
}

export function clinicaWhereClause(product: string, clinicaId: number) {
  const normalized = normalizeApiProduct(product);
  if (normalized === PRODUCT_LAB) {
    return { client: { clinicaIdLab: clinicaId } };
  }
  return { client: { clinicaIdErp: clinicaId } };
}
