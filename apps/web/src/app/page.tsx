import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="app-shell bg-gradient-to-b from-[#e8f4fc] to-[#f5f5f5]">
      <header className="px-4 py-6 md:px-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <span className="text-xl font-bold text-[#0078d4]">InovatiTech Licenças</span>
          <Link href="/login" className="btn btn-primary">
            Painel administrativo
          </Link>
        </div>
      </header>

      <main className="app-main mx-auto flex max-w-6xl flex-col justify-center px-4 py-10 md:px-8">
        <section className="grid gap-8 md:grid-cols-2 md:items-center">
          <div>
            <h1 className="text-3xl font-bold leading-tight md:text-5xl">
              Gerenciamento centralizado de licenças para seus softwares
            </h1>
            <p className="mt-4 text-lg text-muted">
              Excellence Dental Cloud, Dental Lab, VDE Incorporadora e novos produtos SaaS — chaves de 25 caracteres,
              validade, cobrança e NFS-e em um só lugar.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/login" className="btn btn-primary">
                Acessar gerenciador
              </Link>
              <a href="mailto:contato@inovatitech.com.br" className="btn btn-secondary">
                Falar com comercial
              </a>
            </div>
          </div>
          <div className="card">
            <h2 className="text-lg font-semibold">Produtos licenciados</h2>
            <ul className="mt-4 space-y-3 text-sm">
              <li>Excellence Dental Cloud — ERP odontológico</li>
              <li>Dental Lab — laboratório protético</li>
              <li>VDE Incorporadora — em desenvolvimento</li>
              <li>Sites e SaaS — conforme portfólio Inova TI</li>
            </ul>
            <p className="mt-4 text-xs text-muted">
              Alertas automáticos 20, 15, 7, 3, 2 e 1 dia antes do vencimento. Bloqueio após validade com carência
              comercial configurável.
            </p>
          </div>
        </section>
      </main>

      <footer className="px-4 py-6 text-center text-sm text-muted">
        © {new Date().getFullYear()} InovatiTech — licencas.inovatitech.com.br
      </footer>
    </div>
  );
}
