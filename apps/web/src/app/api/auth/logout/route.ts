import { clearSessionCookie } from "@/lib/auth";

export async function GET(req: Request) {
  await clearSessionCookie();
  const url = new URL("/login", req.url);
  return Response.redirect(url);
}

export async function POST() {
  await clearSessionCookie();
  return Response.json({ ok: true });
}
