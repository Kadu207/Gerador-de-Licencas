import Link from "next/link";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/clients", label: "Clientes" },
  { href: "/finance", label: "Financeiro" },
  { href: "/catalog", label: "Catálogo" },
];

export function AppShell({ children, user }: { children: React.ReactNode; user?: string }) {
  return (
    <div className="app-shell">
      <header className="border-b border-border bg-card px-4 py-3 md:px-6">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
          <Link href="/dashboard" className="text-lg font-semibold text-primary">
            Gerenciador de Licenças · InovatiTech
          </Link>
          <nav className="flex flex-wrap gap-3 text-sm font-medium">
            {links.map((l) => (
              <Link key={l.href} href={l.href} className="hover:text-primary">
                {l.label}
              </Link>
            ))}
            <Link href="/api/auth/logout" className="hover:text-primary">
              Sair ({user})
            </Link>
          </nav>
        </div>
      </header>
      <main className="app-main mx-auto w-full max-w-7xl px-4 py-6 md:px-6">{children}</main>
    </div>
  );
}
