import Link from "next/link";
import { loginAction } from "@/lib/actions/auth";

const ERROR_MESSAGES: Record<string, string> = {
  campos: "Informe usuario e senha.",
  credenciais: "Usuario ou senha invalidos.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  const error = params.error ? (ERROR_MESSAGES[params.error] ?? "Nao foi possivel entrar.") : null;

  return (
    <div className="app-shell flex items-center justify-center px-4">
      <div className="card w-full max-w-md">
        <h1 className="text-2xl font-bold">Gerenciador de Licencas</h1>
        <p className="mt-1 text-sm text-muted">Acesso restrito a equipe comercial e suporte.</p>
        {error && <p className="mt-4 rounded-md bg-[#fde7e9] px-3 py-2 text-sm text-[#a4262c]">{error}</p>}
        <form action={loginAction} method="post" className="mt-6 space-y-4">
          <div>
            <label htmlFor="username" className="mb-1 block text-sm font-medium">
              Usuario
            </label>
            <input
              id="username"
              name="username"
              required
              className="input-field"
              autoComplete="username"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium">
              Senha
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              className="input-field"
              autoComplete="current-password"
            />
          </div>
          <button type="submit" className="btn btn-primary w-full">
            Entrar
          </button>
        </form>
        <p className="mt-4 text-center text-sm">
          <Link href="/" className="text-primary hover:underline">
            Voltar ao site
          </Link>
        </p>
      </div>
    </div>
  );
}
