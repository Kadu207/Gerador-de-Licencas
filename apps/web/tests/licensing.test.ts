import { describe, expect, it } from "vitest";
import {
  LICENSE_KEY_LEN,
  PERIOD_3Y,
  PERIOD_DAYS,
  PRODUCT_VDE,
  computeEffectiveStatus,
  generateLicenseKey,
  isValidLicenseKeyFormat,
  normalizeLicenseKey,
  productMatchesLicense,
} from "@/domain/licensing";

describe("licensing domain", () => {
  it("generates 25-char keys", () => {
    const key = generateLicenseKey();
    expect(key).toHaveLength(LICENSE_KEY_LEN);
    expect(isValidLicenseKeyFormat(key)).toBe(true);
  });

  it("validates key format", () => {
    expect(isValidLicenseKeyFormat("SHORT")).toBe(false);
    expect(isValidLicenseKeyFormat("INVALID-CHARS-HERE!!!!")).toBe(false);
  });

  it("normalizes license key", () => {
    const normalized = normalizeLicenseKey("abcd-1234 efgh-5678 ijkl-9012 m");
    expect(normalized).toHaveLength(LICENSE_KEY_LEN);
    expect(normalized).toMatch(/^[A-Z0-9]+$/);
  });

  it("includes 3y period", () => {
    expect(PERIOD_3Y in PERIOD_DAYS).toBe(true);
    expect(PERIOD_DAYS[PERIOD_3Y]).toBe(1095);
  });

  it("keeps independent product licenses", () => {
    expect(productMatchesLicense("cloud", "cloud")).toBe(true);
    expect(productMatchesLicense("lab", "lab")).toBe(true);
    expect(productMatchesLicense("vde", PRODUCT_VDE)).toBe(true);
    expect(productMatchesLicense("cloud", "lab")).toBe(false);
    expect(productMatchesLicense("cloud", "cloud_lab")).toBe(false);
  });

  it("separates validity and payment", () => {
    const now = new Date("2026-01-01T12:00:00Z");
    const ends = new Date("2026-01-11T12:00:00Z");
    const payment = new Date("2026-01-06T12:00:00Z");
    const eff = computeEffectiveStatus({
      manualStatus: "active",
      endsAt: ends,
      paymentDueAt: payment,
      now,
    });
    expect(eff.daysRemaining).toBe(10);
    expect(eff.licenseExpired).toBe(false);
    expect(eff.paymentPhase).toBe("active");
  });

  it("expires license after endsAt", () => {
    const now = new Date("2026-06-01T12:00:00Z");
    const ends = new Date("2026-05-31T12:00:00Z");
    const eff = computeEffectiveStatus({ manualStatus: "active", endsAt: ends, now });
    expect(eff.licenseExpired).toBe(true);
    expect(eff.validForSoftware).toBe(false);
  });
});
