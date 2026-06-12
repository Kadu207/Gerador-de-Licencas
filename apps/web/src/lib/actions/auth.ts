"use server";

import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { prisma } from "@/lib/prisma";
import { ensureBootstrap } from "@/lib/bootstrap";
import { createAccessToken, sessionCookieOptions, verifyPassword } from "@/lib/auth";

export async function loginAction(formData: FormData) {
  await ensureBootstrap();

  const username = String(formData.get("username") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!username || !password) {
    redirect("/login?error=campos");
  }

  const user = await prisma.operator.findUnique({ where: { username } });
  if (!user || !(await verifyPassword(password, user.passwordHash))) {
    redirect("/login?error=credenciais");
  }

  const token = await createAccessToken(user.username);
  const jar = await cookies();
  jar.set("session_token", token, sessionCookieOptions());

  await prisma.auditLog.create({
    data: { operator: user.username, action: "login", detail: "Login no gerenciador" },
  });

  redirect("/dashboard");
}
