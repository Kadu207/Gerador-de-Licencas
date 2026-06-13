import { describe, expect, it } from "vitest";
import type { Client, LicenseRecord } from "@prisma/client";
import {
  boundClinicaId,
  boundToOtherScope,
  clinicaBindingField,
  usesErpClinicaId,
} from "@/lib/services/license-scope";

const baseClient = {
  clinicaIdErp: 100,
  clinicaIdLab: 200,
} as Client;

const baseLic = { unidadeId: null } as LicenseRecord;

describe("license scope Cloud vs Lab", () => {
  it("Cloud usa clinicaIdErp", () => {
    expect(usesErpClinicaId("cloud")).toBe(true);
    expect(boundClinicaId(baseClient, "cloud")).toBe(100);
    expect(clinicaBindingField("cloud")).toBe("clinicaIdErp");
  });

  it("Lab usa clinicaIdLab", () => {
    expect(usesErpClinicaId("lab")).toBe(false);
    expect(boundClinicaId(baseClient, "lab")).toBe(200);
    expect(clinicaBindingField("lab")).toBe("clinicaIdLab");
  });

  it("detecta scope mismatch por produto", () => {
    expect(boundToOtherScope(baseLic, baseClient, 100, null, "cloud")).toBe(false);
    expect(boundToOtherScope(baseLic, baseClient, 200, null, "cloud")).toBe(true);
    expect(boundToOtherScope(baseLic, baseClient, 200, null, "lab")).toBe(false);
    expect(boundToOtherScope(baseLic, baseClient, 100, null, "lab")).toBe(true);
  });
});
