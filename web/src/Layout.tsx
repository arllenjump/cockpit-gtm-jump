import { useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import type { Usuario } from "./App";
import Aprovacoes from "./Aprovacoes";
import Contas from "./Contas";
import ContratoPagina from "./Contrato";
import Lancamentos from "./Lancamentos";
import { aplicarTema, type Tema } from "./tema";

const PAGINAS = [
  { caminho: "/contas", nome: "Contas" },
  { caminho: "/lancamentos", nome: "Lançamentos" },
  { caminho: "/contrato", nome: "Contrato de GTM" },
  { caminho: "/aprovacoes", nome: "Aprovações" },
];

function EmBreve({ nome }: { nome: string }) {
  return (
    <div>
      <h2 className="font-titulo text-2xl font-medium text-grafite dark:text-white">{nome}</h2>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Esta página entra numa próxima etapa.</p>
    </div>
  );
}

function BotaoTema() {
  const [tema, setTema] = useState<Tema>(() =>
    document.documentElement.classList.contains("dark") ? "escuro" : "claro",
  );
  const proximo: Tema = tema === "escuro" ? "claro" : "escuro";

  return (
    <button
      type="button"
      onClick={() => {
        aplicarTema(proximo, true);
        setTema(proximo);
      }}
      className="mt-3 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:border-laranja hover:text-grafite dark:border-white/15 dark:text-slate-300 dark:hover:text-white"
    >
      {tema === "escuro" ? "Usar modo claro" : "Usar modo escuro"}
    </button>
  );
}

export default function Layout({ usuario }: { usuario: Usuario }) {
  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-grafite-escuro">
      <aside className="flex w-60 flex-col border-r border-slate-200 bg-white dark:border-white/10 dark:bg-grafite">
        <div className="px-5 py-6">
          <img src="/logo-jump.png" alt="Jump" className="h-7 dark:hidden" />
          <img src="/logo-jump-branco.png" alt="Jump" className="hidden h-7 dark:block" />
          <div className="mt-2 font-titulo text-sm font-medium tracking-wide text-slate-500 dark:text-slate-300">
            Cockpit GTM
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {PAGINAS.map((p) => (
            <NavLink
              key={p.caminho}
              to={p.caminho}
              className={({ isActive }) =>
                `block rounded-md border-l-4 px-3 py-2 text-sm ${
                  isActive
                    ? "border-laranja bg-orange-50 font-medium text-grafite dark:bg-laranja/15 dark:text-white"
                    : "border-transparent text-slate-600 hover:bg-slate-100 hover:text-grafite dark:text-slate-300 dark:hover:bg-white/5 dark:hover:text-white"
                }`
              }
            >
              {p.nome}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-200 px-5 py-4 text-xs text-slate-500 dark:border-white/10 dark:text-slate-400">
          <div className="truncate">{usuario.email}</div>
          <a
            href="/api/auth/logout"
            className="mt-1 inline-block text-grafite hover:text-laranja-escuro dark:text-slate-200 dark:hover:text-laranja-claro"
          >
            Sair
          </a>
          <div>
            <BotaoTema />
          </div>
        </div>
      </aside>
      <main className="flex-1 p-8">
        <Routes>
          <Route index element={<EmBreve nome="Início" />} />
          <Route path="contas" element={<Contas />} />
          <Route path="lancamentos" element={<Lancamentos />} />
          <Route path="aprovacoes" element={<Aprovacoes />} />
          <Route path="contrato" element={<ContratoPagina />} />
          {PAGINAS.filter((p) => !["/contas", "/lancamentos", "/aprovacoes", "/contrato"].includes(p.caminho)).map((p) => (
            <Route key={p.caminho} path={p.caminho.slice(1)} element={<EmBreve nome={p.nome} />} />
          ))}
        </Routes>
      </main>
    </div>
  );
}
