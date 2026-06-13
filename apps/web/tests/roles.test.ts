import { describe, expect, it } from "vitest";
import {
  ROLE_MASTER,
  ROLE_OPERATOR,
  canCreateCheckout,
  canManageFinance,
  canRevokeLicense,
  isMasterRole,
} from "@/lib/roles";

describe("operator roles", () => {
  it("identifies master role", () => {
    expect(isMasterRole(ROLE_MASTER)).toBe(true);
    expect(isMasterRole("Master")).toBe(true);
  });

  it("treats operator and unknown as non-master", () => {
    expect(isMasterRole(ROLE_OPERATOR)).toBe(false);
    expect(isMasterRole(undefined)).toBe(false);
    expect(isMasterRole("")).toBe(false);
  });

  it("restricts finance, revoke and checkout to master", () => {
    expect(canManageFinance(ROLE_MASTER)).toBe(true);
    expect(canRevokeLicense(ROLE_MASTER)).toBe(true);
    expect(canCreateCheckout(ROLE_MASTER)).toBe(true);

    expect(canManageFinance(ROLE_OPERATOR)).toBe(false);
    expect(canRevokeLicense(ROLE_OPERATOR)).toBe(false);
    expect(canCreateCheckout(ROLE_OPERATOR)).toBe(false);
  });
});
