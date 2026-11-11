import { useSearchParams } from "react-router-dom";

const ERROS: Record<string, string> = {
  dominio: "Acesso permitido só para contas da Jump.",
  sessao: "A sessão de login expirou. Tente de novo.",
};

export default function Login() {
  const [params] = useSearchParams();
  const erro = params.get("erro");

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <img src="/logo-jump.png" alt="Jump" className="h-8" />
        <h1 className="mt-6 font-titulo text-xl font-medium text-grafite">Cockpit GTM</h1>
        <p className="mt-1 text-sm text-slate-500">Entre com sua conta Microsoft da Jump.</p>
        {erro && (
          <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{ERROS[erro] ?? "Não foi possível entrar."}</p>
        )}
        <a
          href="/api/auth/login"
          className="mt-6 block rounded-md bg-laranja px-4 py-2 text-center text-sm font-medium text-white hover:bg-laranja-escuro"
        >
          Entrar com Microsoft
        </a>
      </div>
    </main>
  );
}
