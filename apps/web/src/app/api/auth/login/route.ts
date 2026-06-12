import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ensureBootstrap } from "@/lib/bootstrap";
import { createAccessToken, sessionCookieOptions, verifyPassword } from "@/lib/auth";

export async function POST(req: NextRequest) {
  await ensureBootstrap();
  const { username, password } = await req.json();
  const user = await prisma.operator.findUnique({ where: { username: String(username).trim() } });
  if (!user || !(await verifyPassword(String(password), user.passwordHash))) {
    return NextResponse.json({ error: "Usuario ou senha invalidos." }, { status: 401 });
  }

  const token = await createAccessToken(user.username);
  await prisma.auditLog.create({
    data: { operator: user.username, action: "login", detail: "Login no gerenciador" },
  });

  const response = NextResponse.json({ ok: true });
  response.cookies.set("session_token", token, sessionCookieOptions());
  return response;
}
