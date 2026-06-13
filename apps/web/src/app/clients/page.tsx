import Link from "next/link";
import { redirect } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ClientForm } from "@/components/ClientForm";
import { requireOperator } from "@/lib/auth";
import { ensureBootstrap } from "@/lib/bootstrap";
import { prisma } from "@/lib/prisma";

export default async function ClientsPage() {
  const operator = await requireOperator();
  if (!operator) redirect("/login");
  await ensureBootstrap();

  const [clients, parents] = await Promise.all([
    prisma.client.findMany({ orderBy: { nome: "asc" }, include: { licenses: true } }),
    prisma.client.findMany({ where: { parentClientId: null }, orderBy: { nome: "asc" }, select: { id: true, nome: true } }),
  ]);

  return (
    <AppShell user={operator.username} role={operator.role}>
      <h1 className="text-2xl font-bold">Clientes</h1>
      <p className="text-muted">Cadastro completo com CPF/CNPJ, endereço ViaCEP e matriz/filial.</p>

      <div className="card mt-6">
        <h2 className="font-semibold">Novo cliente</h2>
        <div className="mt-4">
          <ClientForm parents={parents} />
        </div>
      </div>

      <div className="card mt-6 overflow-x-auto">
        <h2 className="font-semibold">Clientes cadastrados</h2>
        <table className="mt-4 w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="py-2">Nome</th>
              <th>Documento</th>
              <th>Licenças</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {clients.map((c) => (
              <tr key={c.id} className="border-b border-border/60">
                <td className="py-2">
                  <strong>{c.nome}</strong>
                  <div className="text-xs text-muted">{c.email}</div>
                </td>
                <td>{c.documentType === "cpf" ? c.cpf : c.cnpj || "—"}</td>
                <td>{c.licenses.length}</td>
                <td>{c.status}</td>
                <td>
                  <Link href={`/clients/${c.id}`} className="text-primary hover:underline">
                    Abrir
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
