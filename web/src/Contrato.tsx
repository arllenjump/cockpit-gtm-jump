import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

type Clausula = {
  clause_key: string;
  strategy: string | null;
  execution: string | null;
  audit_verdict: "alinhado" | "ajustar" | "conflito" | null;
  audit_note: string | null;
};
type Teste = {
  id: number;
  code: string;
  hypothesis: string;
  path_a: string;
  path_b: string;
  fast_signal: string;
  slow_signal: string;
  expected_range: { texto?: string } | null;
  decision_rule: string;
  status: "ativa" | "na_fila" | "decidida";
};
type Aprovacao = { id: number; status: "pendente" | "aprovado" | "ajustado" | "devolvido"; note: string | null; decided_by: string | null; decided_at: string | null };
type Contrato = {
  id: number;
  version: number;
  status: "rascunho" | "em_revisao" | "aprovado" | "substituido";
  created_at: string;
  clausulas: Clausula[];
  testes: Teste[];
  aprovacao: Aprovacao | null;
};
type Versao = { id: number; version: number; status: Contrato["status"] };
type Acao = "aprovar" | "ajustar" | "devolver";

// Itens do contrato (docs/00-contexto.md)
const NOMES: Record<string, string> = {
  icp: "ICP",
  comite: "Comitê de compra",
  categoria: "Categoria",
  gatilhos: "Gatilhos",
  posicionamento: "Posicionamento",
  provas: "Provas",
  estagio: "Estágio da conta",
  validacao: "Validação",
  pausa: "Pausa",
  sucesso: "Sucesso e testes",
};
const STATUS_CONTRATO = { rascunho: "rascunho do agente", em_revisao: "em revisão", aprovado: "aprovado", substituido: "substituído" };
const VEREDITO = {
  alinhado: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  ajustar: "bg-orange-50 text-laranja-escuro dark:bg-laranja/15 dark:text-laranja-claro",
  conflito: "bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-300",
};
const campo =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-laranja focus:outline-none dark:border-white/15 dark:bg-grafite-escuro dark:text-white";
const cartao = "rounded-xl border border-slate-200 bg-white dark:border-white/10 dark:bg-grafite";
const dataHora = (iso: string) => new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

function Linha({
  c,
  editavel,
  salvar,
  ocupado,
}: {
  c: Clausula;
  editavel: boolean;
  salvar: (chave: string, estrategia: string, execucao: string) => Promise<boolean>;
  ocupado: boolean;
}) {
  const [editando, setEditando] = useState(false);
  const [estrategia, setEstrategia] = useState(c.strategy ?? "");
  const [execucao, setExecucao] = useState(c.execution ?? "");

  return (
    <tr className="border-b border-slate-100 align-top last:border-0 dark:border-white/5">
      <td className="whitespace-nowrap px-4 py-3 font-medium text-grafite dark:text-white">{NOMES[c.clause_key] ?? c.clause_key}</td>
      {editando ? (
        <>
          <td className="px-4 py-3">
            <textarea className={campo} rows={4} value={estrategia} onChange={(e) => setEstrategia(e.target.value)} />
          </td>
          <td className="px-4 py-3">
            <textarea className={campo} rows={4} value={execucao} onChange={(e) => setExecucao(e.target.value)} />
          </td>
        </>
      ) : (
        <>
          <td className="px-4 py-3 text-slate-800 dark:text-slate-100">{c.strategy}</td>
          <td className="px-4 py-3 text-slate-800 dark:text-slate-100">{c.execution}</td>
        </>
      )}
      <td className="px-4 py-3">
        {c.audit_verdict && (
          <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${VEREDITO[c.audit_verdict]}`}>{c.audit_verdict}</span>
        )}
        {c.audit_note && <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{c.audit_note}</div>}
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-right">
        {editavel &&
          (editando ? (
            <div className="flex flex-col items-end gap-2">
              <button
                disabled={ocupado}
                onClick={async () => (await salvar(c.clause_key, estrategia, execucao)) && setEditando(false)}
                className="rounded-md bg-laranja px-3 py-1 text-xs font-medium text-white hover:bg-laranja-escuro disabled:opacity-60"
              >
                Salvar
              </button>
              <button
                onClick={() => {
                  setEstrategia(c.strategy ?? "");
                  setExecucao(c.execution ?? "");
                  setEditando(false);
                }}
                className="text-xs text-slate-500 hover:text-grafite dark:hover:text-white"
              >
                Cancelar
              </button>
            </div>
          ) : (
            <button onClick={() => setEditando(true)} className="text-sm text-laranja-escuro hover:underline dark:text-laranja-claro">
              Editar
            </button>
          ))}
      </td>
    </tr>
  );
}

function Decisao({ contrato, decidir, ocupado }: { contrato: Contrato; decidir: (acao: Acao, nota: string) => void; ocupado: boolean }) {
  const [nota, setNota] = useState("");
  const a = contrato.aprovacao;
  const conflitos = contrato.clausulas.filter((c) => c.audit_verdict === "conflito").length;

  if (a && a.status !== "pendente") {
    const texto = { aprovado: "Aprovado", ajustado: "Aprovado com ressalva", devolvido: "Devolvido ao agente" }[a.status];
    return (
      <div className={`${cartao} p-5 text-sm text-slate-700 dark:text-slate-200`}>
        {texto} por {a.decided_by} em {a.decided_at && dataHora(a.decided_at)}
        {a.note && <div className="mt-1">Nota: {a.note}</div>}
        {a.status === "devolvido" && (
          <div className="mt-2">
            Gere a nova versão na página{" "}
            <Link to="/lancamentos" className="text-laranja-escuro hover:underline dark:text-laranja-claro">
              Lançamentos
            </Link>
            ; o agente recebe a instrução.
          </div>
        )}
      </div>
    );
  }
  if (!a) return null;
  return (
    <div className={`${cartao} p-5`}>
      <h3 className="font-titulo text-lg font-medium text-grafite dark:text-white">Sua decisão sobre a versão {contrato.version}</h3>
      {conflitos > 0 && (
        <p className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-500/15 dark:text-red-300">
          A auditoria marcou {conflitos} {conflitos === 1 ? "cláusula" : "cláusulas"} com conflito. Revise antes de aprovar.
        </p>
      )}
      <textarea
        className={`${campo} mt-3`}
        rows={2}
        placeholder="Nota para aprovar com ressalva, ou instrução para o agente refazer"
        value={nota}
        onChange={(e) => setNota(e.target.value)}
      />
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          disabled={ocupado}
          onClick={() => decidir("aprovar", nota)}
          className="rounded-md bg-laranja px-4 py-2 text-sm font-medium text-white hover:bg-laranja-escuro disabled:opacity-60"
        >
          Aprovar contrato
        </button>
        <button
          disabled={ocupado || !nota.trim()}
          onClick={() => decidir("ajustar", nota)}
          className="rounded-md border border-laranja px-4 py-2 text-sm font-medium text-laranja-escuro hover:bg-orange-50 disabled:opacity-40 dark:text-laranja-claro dark:hover:bg-laranja/10"
        >
          Aprovar com ressalva
        </button>
        <button
          disabled={ocupado || !nota.trim()}
          onClick={() => decidir("devolver", nota)}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40 dark:border-white/15 dark:text-slate-200 dark:hover:bg-white/5"
        >
          Devolver ao agente
        </button>
      </div>
      <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
        Aprovar torna esta a versão vigente, marca as anteriores como substituídas e leva o lançamento para a fase 3.
      </p>
    </div>
  );
}

export default function ContratoPagina() {
  const [dados, setDados] = useState<{ contrato: Contrato | null; versoes: Versao[] } | null>(null);
  const [erro, setErro] = useState("");
  const [ocupado, setOcupado] = useState(false);

  const carregar = () =>
    fetch("/api/contratos/atual")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setDados)
      .catch(() => setErro("Não foi possível carregar o contrato."));

  useEffect(() => {
    carregar();
  }, []);

  async function salvar(chave: string, estrategia: string, execucao: string) {
    if (!dados?.contrato) return false;
    setErro("");
    setOcupado(true);
    const r = await fetch(`/api/contratos/${dados.contrato.id}/clausulas/${chave}`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ estrategia, execucao }),
    });
    if (!r.ok) setErro((await r.json().catch(() => null))?.detail ?? "Não foi possível salvar a cláusula.");
    await carregar();
    setOcupado(false);
    return r.ok;
  }

  async function decidir(acao: Acao, nota: string) {
    if (!dados?.contrato) return;
    setErro("");
    setOcupado(true);
    const r = await fetch(`/api/contratos/${dados.contrato.id}/decisao`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ acao, nota }),
    });
    if (!r.ok) setErro((await r.json().catch(() => null))?.detail ?? "Não foi possível registrar a decisão.");
    await carregar();
    setOcupado(false);
  }

  if (!dados) return <p className="text-sm text-slate-500">{erro || "Carregando..."}</p>;
  const { contrato, versoes } = dados;

  if (!contrato) {
    return (
      <div>
        <h2 className="font-titulo text-2xl font-medium text-grafite dark:text-white">Contrato de GTM</h2>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Nenhum contrato ainda. Aprove o estudo e gere o contrato na página{" "}
          <Link to="/lancamentos" className="text-laranja-escuro hover:underline dark:text-laranja-claro">
            Lançamentos
          </Link>
          .
        </p>
      </div>
    );
  }
  const editavel = contrato.status === "rascunho" || contrato.status === "em_revisao";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-titulo text-2xl font-medium text-grafite dark:text-white">Contrato de GTM</h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          OPT-3 · versão {contrato.version} · {STATUS_CONTRATO[contrato.status]} · {dataHora(contrato.created_at)}
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          {versoes.map((v) => (
            <span
              key={v.id}
              className={`rounded-full px-2 py-0.5 ${
                v.id === contrato.id
                  ? "bg-grafite text-white dark:bg-white dark:text-grafite"
                  : "bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300"
              }`}
            >
              v{v.version} {STATUS_CONTRATO[v.status]}
            </span>
          ))}
        </div>
        {editavel && contrato.status === "rascunho" && (
          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
            Ao editar uma cláusula, o cockpit cria a versão {contrato.version + 1} com a sua mudança; a versão do agente fica guardada.
          </p>
        )}
      </div>

      {erro && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-500/15 dark:text-red-300">{erro}</p>}

      <div className={`${cartao} overflow-x-auto`}>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-white/10 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3 font-medium">Cláusula</th>
              <th className="px-4 py-3 font-medium">Estratégia</th>
              <th className="px-4 py-3 font-medium">Execução</th>
              <th className="px-4 py-3 font-medium">Auditoria</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {contrato.clausulas.map((c) => (
              <Linha key={`${contrato.id}-${c.clause_key}`} c={c} editavel={editavel} salvar={salvar} ocupado={ocupado} />
            ))}
          </tbody>
        </table>
      </div>

      <div className={`${cartao} p-5`}>
        <h3 className="font-titulo text-lg font-medium text-grafite dark:text-white">Plano de testes</h3>
        <div className="mt-3 grid gap-4 md:grid-cols-3">
          {contrato.testes.map((t) => (
            <div key={t.id} className="rounded-lg border border-slate-200 p-4 text-sm dark:border-white/10">
              <div className="flex items-center justify-between">
                <span className="font-titulo font-medium text-grafite dark:text-white">{t.code}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    t.status === "ativa"
                      ? "bg-orange-50 text-laranja-escuro dark:bg-laranja/15 dark:text-laranja-claro"
                      : "bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300"
                  }`}
                >
                  {t.status === "ativa" ? "ativa" : t.status === "na_fila" ? "na fila" : "decidida"}
                </span>
              </div>
              <p className="mt-2 text-slate-800 dark:text-slate-100">{t.hypothesis}</p>
              <dl className="mt-2 space-y-1 text-xs text-slate-600 dark:text-slate-300">
                <div>A: {t.path_a}</div>
                <div>B: {t.path_b}</div>
                <div>Sinal rápido: {t.fast_signal}</div>
                <div>Sinal lento: {t.slow_signal}</div>
                <div>Faixa prevista: {t.expected_range?.texto}</div>
                <div>Regra: {t.decision_rule}</div>
              </dl>
            </div>
          ))}
        </div>
      </div>

      <Decisao contrato={contrato} decidir={decidir} ocupado={ocupado} />
    </div>
  );
}
