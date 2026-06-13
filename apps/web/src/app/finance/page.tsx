import { AppShell } from "@/components/AppShell";
import { requireMasterOrRedirect } from "@/lib/auth";
import { getFinanceDashboard } from "@/lib/services/finance-service";
import { PRODUCT_LABELS } from "@/domain/licensing";
import {
  cancelPaymentAction,
  completePaymentAction,
  updatePlanPriceAction,
} from "@/lib/actions/finance";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendente",
  completed: "Confirmado",
  cancelled: "Cancelado",
};

export default async function FinancePage({
  searchParams,
}: {
  searchParams: Promise<{ paid?: string; updated?: string; error?: string }>;
}) {
  const operator = await requireMasterOrRedirect();
  const params = await searchParams;
  const finance = await getFinanceDashboard();

  return (
    <AppShell user={operator.username} role={operator.role}>
      <h1 className="text-2xl font-bold">Gerenciador financeiro</h1>
      <p className="text-muted">
        Vendas de licenças via Stripe (cartão, PIX, boleto pelo Dashboard Brasil). Pagamento confirmado renova a
        validade da licença automaticamente.
      </p>

      {params.paid === "1" && (
        <p className="mt-4 rounded-lg border border-green-500/30 bg-green-500/10 px-4 py-2 text-sm">
          Pagamento recebido — aguardando confirmação do webhook Stripe (ou marque manualmente abaixo).
        </p>
      )}
      {params.updated && (
        <p className="mt-4 rounded-lg border border-primary/30 bg-primary/10 px-4 py-2 text-sm">
          Atualização salva com sucesso.
        </p>
      )}
      {!finance.stripeReady && (
        <p className="mt-4 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm">
          Stripe não configurado: defina <code>STRIPE_SECRET_KEY</code> e <code>STRIPE_WEBHOOK_SECRET</code> no{" "}
          <code>.env</code> da VPS e rode <code>bash infra/ops/provision-web-env.sh</code>.
        </p>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="text-sm text-muted">Receita total</div>
          <div className="text-2xl font-bold">R$ {finance.totalRevenue.toFixed(2)}</div>
        </div>
        <div className="card">
          <div className="text-sm text-muted">Receita no mês</div>
          <div className="text-2xl font-bold">R$ {finance.monthRevenue.toFixed(2)}</div>
        </div>
        <div className="card">
          <div className="text-sm text-muted">Pagamentos pendentes</div>
          <div className="text-2xl font-bold">{finance.pendingCount}</div>
        </div>
        <div className="card">
          <div className="text-sm text-muted">Licenças em risco</div>
          <div className="text-2xl font-bold">{finance.atRiskLicenses.length}</div>
        </div>
      </div>

      {Object.keys(finance.revenueByProduct).length > 0 && (
        <div className="card mt-6">
          <h2 className="font-semibold">Receita por produto</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {Object.entries(finance.revenueByProduct).map(([slug, value]) => (
              <li key={slug} className="flex justify-between border-b border-border/50 py-2">
                <span>{PRODUCT_LABELS[slug] ?? slug}</span>
                <strong>R$ {value.toFixed(2)}</strong>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card mt-6">
        <h2 className="font-semibold">Catálogo e preços (Cloud / Lab)</h2>
        <p className="mt-1 text-sm text-muted">Valores usados no Checkout Stripe e na landing pública.</p>
        <div className="mt-4 space-y-6">
          {finance.catalog
            .filter((p) => p.licenseEnabled)
            .map((product) => (
              <div key={product.id}>
                <h3 className="font-medium">{product.name}</h3>
                <ul className="mt-2 space-y-2">
                  {product.plans.map((plan) => (
                    <li key={plan.id} className="flex flex-wrap items-center gap-3 text-sm">
                      <span className="min-w-[140px]">
                        {plan.name} ({plan.billingPeriod})
                      </span>
                      <form action={updatePlanPriceAction} className="flex items-center gap-2">
                        <input type="hidden" name="plan_id" value={plan.id} />
                        <span>R$</span>
                        <input
                          name="price"
                          type="number"
                          step="0.01"
                          min="0"
                          defaultValue={Number(plan.price)}
                          className="input-field !w-28"
                        />
                        <button type="submit" className="btn btn-secondary text-xs">
                          Salvar
                        </button>
                      </form>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
        </div>
      </div>

      {finance.atRiskLicenses.length > 0 && (
        <div className="card mt-6 overflow-x-auto">
          <h2 className="font-semibold">Licenças com cobrança em atraso</h2>
          <table className="mt-4 w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2">Cliente</th>
                <th>Produto</th>
                <th>Status pagamento</th>
                <th>Vencimento cobrança</th>
              </tr>
            </thead>
            <tbody>
              {finance.atRiskLicenses.map((lic) => (
                <tr key={lic.id} className="border-b border-border/60">
                  <td className="py-2">{lic.client.nome}</td>
                  <td>{PRODUCT_LABELS[lic.produto] ?? lic.produto}</td>
                  <td>{lic.paymentStatus}</td>
                  <td>{lic.paymentDueAt?.toLocaleDateString("pt-BR") ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="card mt-6 overflow-x-auto">
        <h2 className="font-semibold">Histórico de pagamentos</h2>
        <table className="mt-4 w-full min-w-[900px] text-left text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="py-2">Data</th>
              <th>Cliente</th>
              <th>Produto</th>
              <th>Valor</th>
              <th>Plano</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {finance.payments.map((p) => (
              <tr key={p.id} className="border-b border-border/60 align-top">
                <td className="py-2">{p.createdAt.toLocaleDateString("pt-BR")}</td>
                <td>{p.client.nome}</td>
                <td>{p.license ? (PRODUCT_LABELS[p.license.produto] ?? p.license.produto) : "—"}</td>
                <td>R$ {Number(p.amount).toFixed(2)}</td>
                <td>{p.paymentPlan}</td>
                <td>{STATUS_LABELS[p.status] ?? p.status}</td>
                <td>
                  {p.status === "pending" && (
                    <div className="flex flex-col gap-1">
                      <form action={completePaymentAction}>
                        <input type="hidden" name="payment_id" value={p.id} />
                        <button type="submit" className="btn btn-secondary text-xs">
                          Marcar pago
                        </button>
                      </form>
                      <form action={cancelPaymentAction}>
                        <input type="hidden" name="payment_id" value={p.id} />
                        <button type="submit" className="btn btn-danger text-xs">
                          Cancelar
                        </button>
                      </form>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
