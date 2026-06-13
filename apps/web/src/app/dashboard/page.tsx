import { redirect } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { requireOperator } from "@/lib/auth";
import { ensureBootstrap } from "@/lib/bootstrap";
import { prisma } from "@/lib/prisma";
import { effectiveForLicense } from "@/lib/services/license-service";
import { getFinanceSummary } from "@/lib/services/finance-service";

export default async function DashboardPage() {
  const operator = await requireOperator();
  if (!operator) redirect("/login");
  await ensureBootstrap();

  const [clientsCount, licenses, finance, notifications] = await Promise.all([
    prisma.client.count(),
    prisma.licenseRecord.findMany({ orderBy: { id: "desc" }, take: 20, include: { client: true } }),
    getFinanceSummary(),
    prisma.notification.findMany({ where: { read: false }, orderBy: { createdAt: "desc" }, take: 10 }),
  ]);

  return (
    <AppShell user={operator.username} role={operator.role}>
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="text-muted">Visão operacional do gerenciador de licenças.</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="text-sm text-muted">Clientes</div>
          <div className="text-3xl font-bold">{clientsCount}</div>
        </div>
        <div className="card">
          <div className="text-sm text-muted">Licenças recentes</div>
          <div className="text-3xl font-bold">{licenses.length}</div>
        </div>
        <div className="card">
          <div className="text-sm text-muted">Pagamentos pendentes</div>
          <div className="text-3xl font-bold">{finance.pendingCount}</div>
        </div>
        <div className="card">
          <div className="text-sm text-muted">Receita confirmada</div>
          <div className="text-3xl font-bold">R$ {finance.totalRevenue.toFixed(2)}</div>
        </div>
      </div>

      {notifications.length > 0 && (
        <div className="card mt-6">
          <h2 className="font-semibold">Alertas no sistema</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {notifications.map((n) => (
              <li key={n.id}>
                <strong>{n.title}</strong> — {n.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card mt-6 overflow-x-auto">
        <h2 className="font-semibold">Últimas licenças</h2>
        <table className="mt-4 w-full min-w-[640px] text-left text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="py-2">Cliente</th>
              <th>Produto</th>
              <th>Chave</th>
              <th>Validade</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {licenses.map((row) => {
              const eff = effectiveForLicense(row);
              return (
                <tr key={row.id} className="border-b border-border/60">
                  <td className="py-2">{row.client.nome}</td>
                  <td>{row.produto}</td>
                  <td className="mono text-xs">{row.licenseKey}</td>
                  <td>{eff.remainingLabel}</td>
                  <td>
                    <span className={`badge ${eff.validForSoftware ? "badge-active" : "badge-blocked"}`}>
                      {eff.phase}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
