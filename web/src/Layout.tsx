import { NavLink, Route, Routes } from "react-router-dom";
import type { Usuario } from "./App";

const PAGINAS = [
  { caminho: "/contas", nome: "Contas" },
  { caminho: "/lancamentos", nome: "Lançamentos" },
  { caminho: "/contrato", nome: "Contrato de GTM" },
  { caminho: "/aprovacoes", nome: "Aprovações" },
];

function EmBreve({ nome }: { nome: string }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-slate-900">{nome}</h2>
      <p className="mt-2 text-sm text-slate-500">Esta página entra numa próxima etapa.</p>
    </div>
  );
}

export default function Layout({ usuario }: { usuario: Usuario }) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="flex w-60 flex-col border-r border-slate-200 bg-white">
        <div className="px-5 py-5 text-base font-semibold text-slate-900">Cockpit GTM Jump</div>
        <nav className="flex-1 space-y-1 px-3">
          {PAGINAS.map((p) => (
            <NavLink
              key={p.caminho}
              to={p.caminho}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm ${isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"}`
              }
            >
              {p.nome}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-200 px-5 py-4 text-xs text-slate-500">
          <div className="truncate">{usuario.email}</div>
          <a href="/api/auth/logout" className="mt-1 inline-block text-slate-700 hover:underline">
            Sair
          </a>
        </div>
      </aside>
      <main className="flex-1 p-8">
        <Routes>
          <Route index element={<EmBreve nome="Início" />} />
          {PAGINAS.map((p) => (
            <Route key={p.caminho} path={p.caminho.slice(1)} element={<EmBreve nome={p.nome} />} />
          ))}
        </Routes>
      </main>
    </div>
  );
}
