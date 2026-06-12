export const config = {
  secretKey: process.env.SECRET_KEY ?? "change-me-in-production-use-long-random-string",
  adminUsername: process.env.ADMIN_USERNAME ?? "admin",
  adminPassword: process.env.ADMIN_PASSWORD ?? "",
  productApiKey: process.env.PRODUCT_API_KEY ?? "",
  publicBaseUrl: process.env.PUBLIC_BASE_URL ?? "http://127.0.0.1:3000",
  blockAfterDays: Number(process.env.BLOCK_AFTER_DAYS ?? 30),
  cancelAfterDays: Number(process.env.CANCEL_AFTER_DAYS ?? 45),
  stripeSecretKey: process.env.STRIPE_SECRET_KEY ?? "",
  stripeWebhookSecret: process.env.STRIPE_WEBHOOK_SECRET ?? "",
  smtpHost: process.env.SMTP_HOST ?? "",
  smtpUser: process.env.SMTP_USER ?? "",
  smtpPassword: process.env.SMTP_PASSWORD ?? "",
};
