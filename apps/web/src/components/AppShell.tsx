import Link from "next/link";
import { isMasterRole } from "@/lib/roles";

const links = [
  { href: "/dashboard", label: "Dashboard", masterOnly: false },
  { href: "/clients", label: "Clientes", masterOnly: false },
  { href: "/finance", label: "Financeiro", masterOnly: true },
  { href: "/catalog", label: "Catálogo", masterOnly: false },
];

export function AppShell({
  children,
  user,
  role,
}: {
  children: React.ReactNode;
  user?: string;
  role?: string;
}) {
  const master = isMasterRole(role);
  const visibleLinks = links.filter((l) => !l.masterOnly || master);

  return (
    <div className="app-shell">
      <header className="border-b border-border bg-card px-4 py-3 md:px-6">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
          <Link href="/dashboard" className="text-lg font-semibold text-primary">
            Gerenciador de Licenças · InovatiTech
          </Link>
          <nav className="flex flex-wrap items-center gap-3 text-sm font-medium">
            {visibleLinks.map((l) => (
              <Link key={l.href} href={l.href} className="hover:text-primary">
                {l.label}
              </Link>
            ))}
            <span className="text-xs text-muted">
              {user}
              {role ? ` · ${master ? "master" : "operador"}` : ""}
            </span>
            <Link href="/api/auth/logout" className="hover:text-primary">
              Sair
            </Link>
          </nav>
        </div>
      </header>
      <main className="app-main mx-auto w-full max-w-7xl px-4 py-6 md:px-6">{children}</main>
    </div>
  );
}
