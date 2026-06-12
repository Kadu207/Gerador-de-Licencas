import { config } from "@/lib/config";

export async function GET() {
  return Response.json({
    ok: true,
    service: "gerenciador-licencas",
    version: "2.0.0",
    stack: "nextjs",
    publicUrl: config.publicBaseUrl || null,
    productApiConfigured: Boolean(config.productApiKey.trim()),
  });
}
