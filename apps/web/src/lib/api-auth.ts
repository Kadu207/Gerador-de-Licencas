import { timingSafeEqual } from "crypto";
import { config } from "@/lib/config";

export function verifyProductApiKey(header: string | null): boolean {
  const expected = config.productApiKey.trim();
  if (!expected) return false;
  const provided = (header ?? "").trim();
  if (expected.length !== provided.length) return false;
  return timingSafeEqual(Buffer.from(expected), Buffer.from(provided));
}
