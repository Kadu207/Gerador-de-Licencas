import Link from "next/link";
import { redirect, notFound } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { requireOperator } from "@/lib/auth";
import { ensureBootstrap } from "@/lib/bootstrap";
import { prisma } from "@/lib/prisma";
import { PERIOD_LABELS, PRODUCT_LABELS } from "@/domain/licensing";
import { effectiveForLicense } from "@/lib/services/license-service";
import { issueLicenseAction, renewLicenseAction, revokeLicenseAction, checkoutAction } from "@/lib/actions/admin";
import { canCreateCheckout, canRevokeLicense } from "@/lib/roles";
import { listCatalog } from "@/lib/services/catalog-service";

export default async function ClientDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const operator = await requireOperator();
  if (!operator) redirect("/login");
  await ensureBootstrap();

  const { id } = await params;
  const clientId = Number(id);
  const client = await prisma.client.findUnique({
    where: { id: clientId },
    include: { address: true, licenses: { orderBy: { id: "desc" } } },
  });
  if (!client) notFound();

  const catalog = await listCatalog();
  const licensable = catalog.filter((p) => p.licenseEnabled);
  const masterActions = canRevokeLicense(operator.role);
  const canCheckout = canCreateCheckout(operator.role);

  return (
    <AppShell user={operator.username} role={operator.role}>
      <h1 className="text-2xl font-bold">{client.nome}</h1>
      <p className="text-muted">
        {client.documentType === "cpf" ? `CPF ${client.cpf}` : `CNPJ ${client.cnpj}`} · Status: {client.status}
      </p>

      {client.address && (
        <p className="mt-2 text-sm">
          {client.address.logradouro}, {client.address.numero} — {client.address.cidade}/{client.address.uf} · CEP{" "}
          {client.address.cep}
        </p>
      )}

      <div className="card mt-6">
        <h2 className="font-semibold">Emitir nova licença (25 caracteres)</h2>
        <form action={issueLicenseAction} className="mt-4 grid gap-4 md:grid-cols-3">
          <input type="hidden" name="client_id" value={client.id} />
          <div>
            <label className="mb-1 block text-sm font-medium">Software</label>
            <select name="produto" className="input-field" required>
              {licensable.map((p) => (
                <option key={p.slug} value={p.slug}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Período</label>
            <select name="periodo" className="input-field" required>
              {Object.entries(PERIOD_LABELS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Plano pagamento</label>
            <select name="payment_plan" className="input-field">
              <option value="monthly">Mensal</option>
              <option value="semiannual">Semestral</option>
              <option value="annual">Anual</option>
            </select>
          </div>
          <div className="md:col-span-3">
            <button type="submit" className="btn btn-primary">
              Gerar licença
            </button>
          </div>
        </form>
      </div>

      <div className="card mt-6 overflow-x-auto">
        <h2 className="font-semibold">Licenças do cliente</h2>
        <table className="mt-4 w-full min-w-[900px] text-left text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="py-2">Chave</th>
              <th>Produto</th>
              <th>Período</th>
              <th>Restante</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {client.licenses.map((lic) => {
              const eff = effectiveForLicense(lic);
              return (
                <tr key={lic.id} className="border-b border-border/60 align-top">
                  <td className="mono py-2 text-xs">{lic.licenseKey}</td>
                  <td>{PRODUCT_LABELS[lic.produto] ?? lic.produto}</td>
                  <td>{PERIOD_LABELS[lic.periodo] ?? lic.periodo}</td>
                  <td>{eff.remainingLabel}</td>
                  <td>
                    <span className={`badge ${eff.validForSoftware ? "badge-active" : "badge-blocked"}`}>
                      {eff.phase}
                    </span>
                    <div className="mt-1 text-xs text-muted">{eff.message}</div>
                  </td>
                  <td>
                    <div className="flex flex-col gap-2">
                      <form action={renewLicenseAction} className="flex gap-2">
                        <input type="hidden" name="license_id" value={lic.id} />
                        <select name="periodo" className="input-field !w-auto min-w-[120px]">
                          {Object.entries(PERIOD_LABELS).map(([k, v]) => (
                            <option key={k} value={k}>
                              {v}
                            </option>
                          ))}
                        </select>
                        <button type="submit" className="btn btn-secondary">
                          Renovar
                        </button>
                      </form>
                      {canCheckout && (
                        <form action={checkoutAction} className="flex gap-2">
                          <input type="hidden" name="client_id" value={client.id} />
                          <input type="hidden" name="license_id" value={lic.id} />
                          <input type="hidden" name="produto" value={lic.produto} />
                          <select name="payment_plan" className="input-field !w-auto">
                            <option value="monthly">Mensal</option>
                            <option value="semiannual">Semestral</option>
                            <option value="annual">Anual</option>
                          </select>
                          <button type="submit" className="btn btn-secondary">
                            Link pagamento
                          </button>
                        </form>
                      )}
                      {masterActions && (
                        <form action={revokeLicenseAction}>
                          <input type="hidden" name="license_id" value={lic.id} />
                          <input type="hidden" name="reason" value="Revogação manual" />
                          <button type="submit" className="btn btn-danger">
                            Revogar
                          </button>
                        </form>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-6">
        <Link href="/clients" className="text-primary hover:underline">
          ← Voltar para clientes
        </Link>
      </p>
    </AppShell>
  );
}
