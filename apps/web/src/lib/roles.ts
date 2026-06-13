export const ROLE_MASTER = "master";
export const ROLE_OPERATOR = "operator";

export function isMasterRole(role: string | null | undefined): boolean {
  return (role ?? ROLE_OPERATOR).toLowerCase() === ROLE_MASTER;
}

export function canManageFinance(role: string | null | undefined): boolean {
  return isMasterRole(role);
}

export function canRevokeLicense(role: string | null | undefined): boolean {
  return isMasterRole(role);
}

export function canCreateCheckout(role: string | null | undefined): boolean {
  return isMasterRole(role);
}
