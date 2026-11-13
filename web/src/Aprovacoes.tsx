import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

type Item = {
  id: number;
  item_type: "lista_contas" | "estudo" | "contrato";
  item_id: number;
  phase: number;
  summary: string;
  status: "pendente" | "aprovado" | "ajustado" | "devolvido";
  note: string | null;
  decided_by: string | null;
  decided_at: string | null;
  created_at: string;
};
type Acao = "aprovar" | "ajustar" | "devolver";

const TIPOS = {
  lista_contas: { nome: "Lista de contas", pagina: "/contas" },
  estudo: { nome: "Estudo", pagina: "/lancamentos" },
  contrato: { nome: "Contrato de GTM", pagina: "/contrato" },
};
const STATUS = {
  pendente: { texto: "Pendente", cor: "bg-orange-50 text-laranja-escuro dark:bg-laranja/15 dark:text-laranja-claro" },
  aprovado: { texto: "Aprovado", cor: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300" },
  ajustado: { texto: "Aprovado com ressalva", cor: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300" },
  devolvido: { texto: "Devolvido ao agente", cor: "bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200" },
};
const dataHora = (iso: string) => new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
const cartao = "rounded-xl border border-slate-200 bg-white p-5 dark:border-white/10 dark:bg-grafite";

function Etiqueta({ status }: { status: Item["status"] }) {
  return <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${STATUS[status].cor}`}>{STATUS[status].texto}</span>;
}

function Pendente({ item, decidir, ocupado }: { item: Item; decidir: (id: number, acao: Acao, nota: string) => void; ocupado: boolean }) {
  const [nota, setNota] = useState("");
  const tipo = TIPOS[item.item_type];
  return (
    <div className={cartao}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {tipo.nome} · fase {item.phase}
          </div>
          <div className="mt-1 font-medium text-grafite dark:text-white">{item.summary}</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">Na fila desde {dataHora(item.created_at)}</div>
        </div>
        <Link to={tipo.pagina} className="text-sm text-laranja-escuro hover:underline dark:text-laranja-claro">
          Abrir
        </Link>
      </div>
      <textarea
        className="mt-4 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-laranja focus:outline-none dark:border-white/15 dark:bg-grafite-escuro dark:text-white"
        rows={2}
        placeholder="Nota para aprovar com ressalva, ou instrução para o agente refazer"
        value={nota}
        onChange={(e) => setNota(e.target.value)}
      />
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          disabled={ocupado}
          onClick={() => decidir(item.id, "aprovar", nota)}
          className="rounded-md bg-laranja px-4 py-2 text-sm font-medium text-white hover:bg-laranja-escuro disabled:opacity-60"
        >
          Aprovar
        </button>
        <button
          disabled={ocupado || !nota.trim()}
          onClick={() => decidir(item.id, "ajustar", nota)}
          className="rounded-md border border-laranja px-4 py-2 text-sm font-medium text-laranja-escuro hover:bg-orange-50 disabled:opacity-40 dark:text-laranja-claro dark:hover:bg-laranja/10"
        >
          Aprovar com ressalva
        </button>
        <button
          disabled={ocupado || !nota.trim()}
          onClick={() => decidir(item.id, "devolver", nota)}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40 dark:border-white/15 dark:text-slate-200 dark:hover:bg-white/5"
        >
          Devolver ao agente
        </button>
      </div>
    </div>
  );
}

export default function Aprovacoes() {
  const [dados, setDados] = useState<{ pendentes: Item[]; decididos: Item[] } | null>(null);
  const [erro, setErro] = useState("");
  const [ocupado, setOcupado] = useState(false);

  const carregar = () =>
    fetch("/api/aprovacoes")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setDados)
      .catch(() => setErro("Não foi possível carregar a fila."));

  useEffect(() => {
    carregar();
  }, []);

  async function decidir(id: number, acao: Acao, nota: string) {
    setErro("");
    setOcupado(true);
    const r = await fetch(`/api/aprovacoes/${id}/decisao`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ acao, nota }),
    });
    if (!r.ok) setErro((await r.json().catch(() => null))?.detail ?? "Não foi possível registrar a decisão.");
    await carregar();
    setOcupado(false);
  }

  if (!dados) return <p className="text-sm text-slate-500">{erro || "Carregando..."}</p>;

  return (
    <div className="max-w-4xl">
      <h2 className="font-titulo text-2xl font-medium text-grafite dark:text-white">Aprovações</h2>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        Nada que fala com o mercado sai sem uma decisão registrada aqui.
      </p>
      {erro && <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-500/15 dark:text-red-300">{erro}</p>}

      <h3 className="mt-8 font-titulo text-lg font-medium text-grafite dark:text-white">
        Pendentes <span className="text-slate-400">({dados.pendentes.length})</span>
      </h3>
      <div className="mt-3 space-y-4">
        {dados.pendentes.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Nada esperando decisão.</p>
        ) : (
          dados.pendentes.map((i) => <Pendente key={i.id} item={i} decidir={decidir} ocupado={ocupado} />)
        )}
      </div>

      <h3 className="mt-10 font-titulo text-lg font-medium text-grafite dark:text-white">Decididos recentemente</h3>
      <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-white/10 dark:bg-grafite">
        {dados.decididos.length === 0 ? (
          <p className="p-5 text-sm text-slate-500 dark:text-slate-400">Nenhuma decisão ainda.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-white/10 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Item</th>
                <th className="px-4 py-3 font-medium">Decisão</th>
                <th className="px-4 py-3 font-medium">Quem e quando</th>
              </tr>
            </thead>
            <tbody>
              {dados.decididos.map((i) => (
                <tr key={i.id} className="border-b border-slate-100 align-top last:border-0 dark:border-white/5">
                  <td className="px-4 py-3">
                    <div className="text-xs text-slate-500 dark:text-slate-400">{TIPOS[i.item_type].nome}</div>
                    <div className="text-grafite dark:text-white">{i.summary}</div>
                    {i.note && <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">Nota: {i.note}</div>}
                  </td>
                  <td className="px-4 py-3">
                    <Etiqueta status={i.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-200">
                    <div>{i.decided_by}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">{i.decided_at && dataHora(i.decided_at)}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
