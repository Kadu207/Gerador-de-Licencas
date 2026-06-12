import { SignJWT, jwtVerify } from "jose";
import bcrypt from "bcryptjs";
import { cookies } from "next/headers";
import { config } from "@/lib/config";

const ALGORITHM = "HS256";
const COOKIE_NAME = "session_token";
const TTL_MINUTES = 480;

function secretKey() {
  return new TextEncoder().encode(config.secretKey);
}

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: config.publicBaseUrl.startsWith("https"),
    maxAge: TTL_MINUTES * 60,
    path: "/",
  };
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 12);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export async function createAccessToken(subject: string): Promise<string> {
  return new SignJWT({ sub: subject })
    .setProtectedHeader({ alg: ALGORITHM })
    .setExpirationTime(`${TTL_MINUTES}m`)
    .sign(secretKey());
}

export async function decodeToken(token: string): Promise<string | null> {
  try {
    const { payload } = await jwtVerify(token, secretKey());
    const sub = payload.sub;
    return typeof sub === "string" ? sub : null;
  } catch {
    return null;
  }
}

export async function setSessionCookie(token: string) {
  const jar = await cookies();
  jar.set(COOKIE_NAME, token, sessionCookieOptions());
}

export async function clearSessionCookie() {
  const jar = await cookies();
  jar.delete(COOKIE_NAME);
}

export async function getSessionUsername(): Promise<string | null> {
  const jar = await cookies();
  const token = jar.get(COOKIE_NAME)?.value;
  if (!token) return null;
  return decodeToken(token);
}

export async function requireOperator() {
  const username = await getSessionUsername();
  if (!username) return null;
  const { prisma } = await import("@/lib/prisma");
  return prisma.operator.findFirst({ where: { username, ativo: true } });
}
