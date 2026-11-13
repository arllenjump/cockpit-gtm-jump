import { useEffect, useState } from "react";

type Estudo = {
  mercado: string;
  concorrentes: { nome: string; movimento: string; implicacao: string }[];
  oportunidades: { titulo: string; porque: string; impacto: "baixo" | "medio" | "alto" }[];
  riscos: string[];
  perguntas_em_aberto: string[];
  fontes: { lidas: string[]; ausentes: string[] };
};
type Dados = {
  produto: string;
  lancamento: null | {
    id: number;
    phase: number;
    created_by: string;
    started_at: string;
    objetivo: string;
    contexto: string;
    provas: string;
    prazo_dias: number;
  };
  estudo: null | {
    id: number;
    content: Estudo;
    status: string;
    created_at: string;
    aprovacao: "pendente" | "aprovado" | "ajustado" | "devolvido" | null;
    nota: string | null;
    decided_by: string | null;
    decided_at: string | null;
  };
  custo: { gasto_usd: number; teto_usd: number; alerta: boolean };
  contrato: null | { id: number; version: number; status: string; created_at: string; alinhado: number; ajustar: number; conflito: number };
};

const FONTES = ["martech-monitor", "ICP Jump", "Jump Bases"];
const IMPACTO = {
  alto: "bg-orange-50 text-laranja-escuro dark:bg-laranja/15 dark:text-laranja-claro",
  medio: "bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200",
  baixo: "bg-slate-50 text-slate-500 dark:bg-white/5 dark:text-slate-400",
};
const campo =
  "mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-laranja focus:outline-none dark:border-white/15 dark:bg-grafite-escuro dark:text-white";
const cartao = "rounded-xl border border-slate-200 bg-white p-6 dark:border-white/10 dark:bg-grafite";
const titulo = "text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400";

function Lista({ itens }: { itens: string[] }) {
  return (
    <ul className="list-disc space-y-1 pl-4 text-sm text-slate-800 dark:text-slate-100">
      {itens.map((i) => (
        <li key={i}>{i}</li>
      ))}
    </ul>
  );
}

function VerEstudo({ estudo }: { estudo: Estudo }) {
  return (
    <div className="space-y-6">
      <section>
        <h4 className={titulo}>Mercado</h4>
        <p className="mt-1 text-sm text-slate-800 dark:text-slate-100">{estudo.mercado}</p>
      </section>
      <section>
        <h4 className={titulo}>Concorrentes</h4>
        <div className="mt-2 space-y-3">
          {estudo.concorrentes.map((c) => (
            <div key={c.nome} className="text-sm">
              <div className="font-medium text-grafite dark:text-white">{c.nome}</div>
              <div className="text-slate-700 dark:text-slate-200">{c.movimento}</div>
              <div className="text-slate-500 dark:text-slate-400">Implicação: {c.implicacao}</div>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h4 className={titulo}>Oportunidades</h4>
        <div className="mt-2 space-y-3">
          {estudo.oportunidades.map((o) => (
            <div key={o.titulo} className="text-sm">
              <span className={`mr-2 rounded-full px-2 py-0.5 text-xs font-medium ${IMPACTO[o.impacto]}`}>impacto {o.impacto}</span>
              <span className="font-medium text-grafite dark:text-white">{o.titulo}</span>
              <div className="mt-0.5 text-slate-700 dark:text-slate-200">{o.porque}</div>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h4 className={titulo}>Riscos</h4>
        <div className="mt-1">
          <Lista itens={estudo.riscos} />
        </div>
      </section>
      <section>
        <h4 className={titulo}>Perguntas em aberto</h4>
        <div className="mt-1">
          <Lista itens={estudo.perguntas_em_aberto} />
        </div>
      </section>
    </div>
  );
}

function Fontes({ gerando, fontes }: { gerando: boolean; fontes?: Estudo["fontes"] }) {
  return (
    <ul className="space-y-2 text-sm">
      {FONTES.map((f) => {
        const lida = fontes?.lidas.includes(f);
        const ausente = fontes?.ausentes.includes(f);
        const estado = gerando ? "lendo..." : lida ? "lida" : ausente ? "ausente" : "aguardando";
        const cor = lida
          ? "text-emerald-700 dark:text-emerald-300"
          : ausente
            ? "text-slate-400"
            : "text-laranja-escuro dark:text-laranja-claro";
        return (
          <li key={f} className="flex justify-between gap-4">
            <span className="text-slate-800 dark:text-slate-100">{f}</span>
            <span className={cor}>{estado}</span>
          </li>
        );
      })}
    </ul>
  );
}

const dataHora = (iso: string) => new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

function Decisao({
  estudo,
  aoDecidir,
  aoRefazer,
  ocupado,
}: {
  estudo: NonNullable<Dados["estudo"]>;
  aoDecidir: (acao: "aprovar" | "ajustar" | "devolver", nota: string) => void;
  aoRefazer: () => void;
  ocupado: boolean;
}) {
  const [nota, setNota] = useState("");

  if (estudo.aprovacao === "pendente") {
    return (
      <div className="mt-8 border-t border-slate-200 pt-6 dark:border-white/10">
        <h4 className={titulo}>Sua decisão</h4>
        <textarea
          className={campo}
          rows={2}
          placeholder="Nota para aprovar com ressalva, ou instrução para o agente refazer"
          value={nota}
          onChange={(e) => setNota(e.target.value)}
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            disabled={ocupado}
            onClick={() => aoDecidir("aprovar", nota)}
            className="rounded-md bg-laranja px-4 py-2 text-sm font-medium text-white hover:bg-laranja-escuro disabled:opacity-60"
          >
            Aprovar
          </button>
          <button
            disabled={ocupado || !nota.trim()}
            onClick={() => aoDecidir("ajustar", nota)}
            className="rounded-md border border-laranja px-4 py-2 text-sm font-medium text-laranja-escuro hover:bg-orange-50 disabled:opacity-40 dark:text-laranja-claro dark:hover:bg-laranja/10"
          >
            Aprovar com ressalva
          </button>
          <button
            disabled={ocupado || !nota.trim()}
            onClick={() => aoDecidir("devolver", nota)}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40 dark:border-white/15 dark:text-slate-200 dark:hover:bg-white/5"
          >
            Devolver ao agente
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Aprovar ou aprovar com ressalva leva o lançamento para a fase 2. Devolver pede uma nova versão do estudo.
        </p>
      </div>
    );
  }

  if (!estudo.aprovacao || !estudo.decided_by || !estudo.decided_at) return null;
  const textos = {
    aprovado: "Aprovado",
    ajustado: "Aprovado com ressalva",
    devolvido: "Devolvido ao agente",
  } as const;
  const devolvido = estudo.aprovacao === "devolvido";
  return (
    <div className="mt-8 border-t border-slate-200 pt-6 dark:border-white/10">
      <p
        className={`rounded-md px-3 py-2 text-sm ${
          devolvido
            ? "bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200"
            : "bg-emerald-50 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300"
        }`}
      >
        {textos[estudo.aprovacao]} por {estudo.decided_by} em {dataHora(estudo.decided_at)}
        {!devolvido && " · lançamento na fase 2"}
      </p>
      {estudo.nota && (
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">
          {devolvido ? "Instrução" : "Ressalva"}: {estudo.nota}
        </p>
      )}
      {devolvido && (
        <button
          disabled={ocupado}
          onClick={aoRefazer}
          className="mt-3 rounded-md bg-laranja px-4 py-2 text-sm font-medium text-white hover:bg-laranja-escuro disabled:opacity-60"
        >
          {ocupado ? "Refazendo..." : "Refazer o estudo com a instrução"}
        </button>
      )}
    </div>
  );
}

export default function Lancamentos() {
  const [dados, setDados] = useState<Dados | null>(null);
  const [form, setForm] = useState({ objetivo: "", contexto: "", provas: "", prazo_dias: 42 });
  const [gerando, setGerando] = useState(false);
  const [erro, setErro] = useState("");
  const [novo, setNovo] = useState(false);

  const carregar = () =>
    fetch("/api/lancamentos")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setDados)
      .catch(() => setErro("Não foi possível carregar o lançamento."));

  useEffect(() => {
    carregar();
  }, []);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setGerando(true);
    try {
      const r = await fetch("/api/lancamentos", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!r.ok) throw new Error("Não foi possível salvar o briefing.");
      const { id } = await r.json();
      setNovo(false);
      setForm({ objetivo: "", contexto: "", provas: "", prazo_dias: 42 });
      await carregar();
      const e2 = await fetch(`/api/lancamentos/${id}/estudo`, { method: "POST" });
      if (!e2.ok) throw new Error((await e2.json().catch(() => null))?.detail ?? "O agente de estudo falhou.");
    } catch (err) {
      setErro(err instanceof Error ? err.message : "O agente de estudo falhou.");
    }
    await carregar();
    setGerando(false);
  }

  async function decidir(acao: "aprovar" | "ajustar" | "devolver", nota: string) {
    if (!dados?.estudo) return;
    setErro("");
    setGerando(true);
    const r = await fetch(`/api/lancamentos/estudos/${dados.estudo.id}/decisao`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ acao, nota }),
    });
    if (!r.ok) setErro((await r.json().catch(() => null))?.detail ?? "Não foi possível registrar a decisão.");
    await carregar();
    setGerando(false);
  }

  async function gerarContrato() {
    if (!dados?.lancamento) return;
    setErro("");
    setGerando(true);
    const r = await fetch(`/api/lancamentos/${dados.lancamento.id}/contrato`, { method: "POST" });
    if (!r.ok) setErro((await r.json().catch(() => null))?.detail ?? "O agente de contrato falhou.");
    await carregar();
    setGerando(false);
  }

  async function refazer() {
    if (!dados?.lancamento) return;
    setErro("");
    setGerando(true);
    const r = await fetch(`/api/lancamentos/${dados.lancamento.id}/estudo`, { method: "POST" });
    if (!r.ok) setErro((await r.json().catch(() => null))?.detail ?? "O agente de estudo falhou.");
    await carregar();
    setGerando(false);
  }

  if (!dados) return <p className="text-sm text-slate-500">{erro || "Carregando..."}</p>;
  const { lancamento, estudo, custo, contrato } = dados;

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-titulo text-2xl font-medium text-grafite dark:text-white">Lançamentos</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {dados.produto} · {lancamento && lancamento.phase >= 2 ? "fase 2: criação do GTM" : "fase 1: briefing e estudo"}
          </p>
        </div>
        <p className={`text-xs ${custo.alerta ? "font-medium text-red-600 dark:text-red-300" : "text-slate-500 dark:text-slate-400"}`}>
          Gasto com a Claude no mês: US$ {custo.gasto_usd.toFixed(2)} de US$ {custo.teto_usd.toFixed(0)}
          {custo.alerta && " · acima de 80% do teto"}
        </p>
      </div>

      {erro && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-500/15 dark:text-red-300">{erro}</p>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[380px_1fr]">
        <div className="space-y-6">
          {lancamento && !novo ? (
            <div className={cartao}>
              <h3 className="font-titulo text-lg font-medium text-grafite dark:text-white">Briefing</h3>
              <dl className="mt-4 space-y-3 text-sm">
                {(
                  [
                    ["Produto", dados.produto],
                    ["Objetivo", lancamento.objetivo],
                    ["Contexto", lancamento.contexto || "Não informado"],
                    ["Provas", lancamento.provas || "Não informadas"],
                    ["Prazo", `${lancamento.prazo_dias} dias`],
                  ] as const
                ).map(([rotulo, valor]) => (
                  <div key={rotulo}>
                    <dt className={titulo}>{rotulo}</dt>
                    <dd className="mt-0.5 text-slate-800 dark:text-slate-100">{valor}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
                Lançamento aberto por {lancamento.created_by} em {dataHora(lancamento.started_at)}.
              </p>
              <button
                type="button"
                disabled={gerando}
                onClick={() => {
                  if (window.confirm("Começar um novo lançamento do OPT-3? O lançamento atual fica guardado, mas esta página passa a mostrar o novo.")) setNovo(true);
                }}
                className="mt-4 w-full rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-60 dark:border-white/15 dark:text-slate-200 dark:hover:bg-white/5"
              >
                Começar novo lançamento
              </button>
            </div>
          ) : (
            <form onSubmit={enviar} className={cartao}>
            <h3 className="font-titulo text-lg font-medium text-grafite dark:text-white">Briefing</h3>
            <label className="mt-4 block text-sm text-slate-700 dark:text-slate-200">
              Produto
              <input className={campo} value={dados.produto} disabled />
            </label>
            <label className="mt-3 block text-sm text-slate-700 dark:text-slate-200">
              Objetivo
              <textarea
                className={campo}
                rows={3}
                required
                value={form.objetivo}
                onChange={(e) => setForm({ ...form, objetivo: e.target.value })}
              />
            </label>
            <label className="mt-3 block text-sm text-slate-700 dark:text-slate-200">
              Contexto
              <textarea className={campo} rows={3} value={form.contexto} onChange={(e) => setForm({ ...form, contexto: e.target.value })} />
            </label>
            <label className="mt-3 block text-sm text-slate-700 dark:text-slate-200">
              Provas
              <textarea className={campo} rows={2} value={form.provas} onChange={(e) => setForm({ ...form, provas: e.target.value })} />
            </label>
            <label className="mt-3 block text-sm text-slate-700 dark:text-slate-200">
              Prazo (dias)
              <input
                className={campo}
                type="number"
                min={1}
                max={365}
                value={form.prazo_dias}
                onChange={(e) => setForm({ ...form, prazo_dias: Number(e.target.value) })}
              />
            </label>
            <button
              type="submit"
              disabled={gerando}
              className="mt-5 w-full rounded-md bg-laranja px-4 py-2 text-sm font-medium text-white hover:bg-laranja-escuro disabled:opacity-60"
            >
              {gerando ? "Gerando o estudo..." : "Enviar ao agente de estudo"}
            </button>
            {lancamento && (
              <button
                type="button"
                onClick={() => setNovo(false)}
                className="mt-2 w-full text-sm text-slate-500 hover:text-grafite dark:hover:text-white"
              >
                Cancelar e voltar ao lançamento atual
              </button>
            )}
            </form>
          )}

          {lancamento && lancamento.phase >= 2 && (
            <div className={cartao}>
              <h3 className="font-titulo text-lg font-medium text-grafite dark:text-white">Contrato de GTM</h3>
              {contrato ? (
                <div className="mt-3 text-sm text-slate-700 dark:text-slate-200">
                  <div>
                    Versão {contrato.version} · {contrato.status} · {dataHora(contrato.created_at)}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300">
                      {contrato.alinhado} alinhado
                    </span>
                    <span className="rounded-full bg-orange-50 px-2 py-0.5 text-laranja-escuro dark:bg-laranja/15 dark:text-laranja-claro">
                      {contrato.ajustar} ajustar
                    </span>
                    <span className="rounded-full bg-red-50 px-2 py-0.5 text-red-700 dark:bg-red-500/15 dark:text-red-300">
                      {contrato.conflito} conflito
                    </span>
                  </div>
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
                  Estudo aprovado. O agente de contrato escreve as 10 cláusulas e o plano de testes, e a auditoria revisa cada cláusula.
                </p>
              )}
              <button
                disabled={gerando}
                onClick={gerarContrato}
                className="mt-4 w-full rounded-md bg-laranja px-4 py-2 text-sm font-medium text-white hover:bg-laranja-escuro disabled:opacity-60"
              >
                {gerando ? "Gerando..." : contrato ? "Gerar nova versão do contrato" : "Gerar contrato de GTM"}
              </button>
            </div>
          )}

          <div className={cartao}>
            <h3 className="font-titulo text-lg font-medium text-grafite dark:text-white">Fontes</h3>
            <div className="mt-3">
              <Fontes gerando={gerando} fontes={estudo?.content.fontes} />
            </div>
          </div>
        </div>

        <div className={cartao}>
          {estudo ? (
            <>
              <div className="mb-6 flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="font-titulo text-lg font-medium text-grafite dark:text-white">Estudo</h3>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {estudo.status} · {dataHora(estudo.created_at)}
                </span>
              </div>
              {lancamento && (
                <p className="mb-6 text-sm text-slate-500 dark:text-slate-400">Objetivo: {lancamento.objetivo}</p>
              )}
              <VerEstudo estudo={estudo.content} />
              <Decisao estudo={estudo} aoDecidir={decidir} aoRefazer={refazer} ocupado={gerando} />
            </>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {gerando ? "O agente está lendo as fontes e escrevendo o estudo." : "Preencha o briefing e envie ao agente de estudo."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
