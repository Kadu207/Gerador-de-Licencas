import { redirect } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { requireOperator } from "@/lib/auth";
import { ensureBootstrap } from "@/lib/bootstrap";
import { listCatalog } from "@/lib/services/catalog-service";

const STATUS_LABELS: Record<string, string> = {
  active: "Disponível",
  construction: "Em construção",
  planned: "Em breve",
};

export default async function CatalogPage() {
  const operator = await requireOperator();
  if (!operator) redirect("/login");
  await ensureBootstrap();

  const products = await listCatalog();

  return (
    <AppShell user={operator.username}>
      <h1 className="text-2xl font-bold">Catálogo de produtos</h1>
      <p className="text-muted">
        Portfólio Inova TI — sites, SaaS e softwares sob licenciamento. Novos produtos podem ser adicionados conforme
        forem desenvolvidos.
      </p>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {products.map((p) => (
          <div key={p.id} className="card">
            <div className="flex items-start justify-between gap-2">
              <h2 className="text-lg font-semibold">{p.name}</h2>
              <span className="badge badge-active">{STATUS_LABELS[p.status] ?? p.status}</span>
            </div>
            <p className="mt-2 text-sm text-muted">{p.description}</p>
            <p className="mt-2 text-xs">
              Slug: <code>{p.slug}</code> · Licenciável: {p.licenseEnabled ? "Sim" : "Não"}
            </p>
            {p.plans.length > 0 && (
              <ul className="mt-4 space-y-2 text-sm">
                {p.plans.map((plan) => (
                  <li key={plan.id} className="flex justify-between border-t border-border/60 pt-2">
                    <span>
                      {plan.name} ({plan.billingPeriod})
                    </span>
                    <strong>{Number(plan.price) > 0 ? `R$ ${Number(plan.price).toFixed(2)}` : "Sob consulta"}</strong>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </AppShell>
  );
}
