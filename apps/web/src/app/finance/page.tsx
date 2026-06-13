import { redirect } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { requireMasterOrRedirect } from "@/lib/auth";
import { getFinanceSummary } from "@/lib/services/finance-service";

export default async function FinancePage() {
  const operator = await requireMasterOrRedirect();

  const finance = await getFinanceSummary();

  return (
    <AppShell user={operator.username} role={operator.role}>
      <h1 className="text-2xl font-bold">Gerenciador financeiro</h1>
      <p className="text-muted">
        Cobranças Stripe (cartão, PIX, boleto via Dashboard Brasil) vinculadas às licenças emitidas.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <div className="card">
          <div className="text-sm text-muted">Receita confirmada</div>
          <div className="text-2xl font-bold">R$ {finance.totalRevenue.toFixed(2)}</div>
        </div>
        <div className="card">
          <div className="text-sm text-muted">Pagamentos pendentes</div>
          <div className="text-2xl font-bold">{finance.pendingCount}</div>
        </div>
        <div className="card">
          <div className="text-sm text-muted">Produtos licenciáveis</div>
          <div className="text-2xl font-bold">{finance.activeProducts}</div>
        </div>
      </div>

      <div className="card mt-6 overflow-x-auto">
        <h2 className="font-semibold">Histórico de pagamentos</h2>
        <table className="mt-4 w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="py-2">Data</th>
              <th>Cliente</th>
              <th>Produto</th>
              <th>Valor</th>
              <th>Plano</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {finance.payments.map((p) => (
              <tr key={p.id} className="border-b border-border/60">
                <td className="py-2">{p.createdAt.toLocaleDateString("pt-BR")}</td>
                <td>{p.client.nome}</td>
                <td>{p.license?.produto ?? "—"}</td>
                <td>R$ {Number(p.amount).toFixed(2)}</td>
                <td>{p.paymentPlan}</td>
                <td>{p.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
