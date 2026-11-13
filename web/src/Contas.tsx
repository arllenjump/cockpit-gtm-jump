import { useEffect, useState } from "react";

type Sinal = { type: string; detail: string; date: string };
type Decisor = { role: string; area: string; is_decision_maker: boolean };
type Conta = {
  external_id: string;
  name: string;
  sector: string;
  employees: number;
  gtm_score: number;
  tier: string;
  signals: Sinal[];
  decision_makers: Decisor[];
  dossier: {
    why_now: string;
    why_us: string;
    suggested_approach: string;
    risks: string[];
    recommended_offer: string;
  };
};
type Validacao = { id: number; validated_by: string; validated_at: string; total: number };
type Resposta = { simulacao: boolean; semana: string; validacao: Validacao | null; contas: Conta[] };

// Tradução dos sinais (docs/03-integracoes.md)
const SINAIS: Record<string, { texto: string; tipo: "positivo" | "neutro" | "reativo" }> = {
  capital_investment: { texto: "Investimento recente", tipo: "positivo" },
  expansion: { texto: "Expansão", tipo: "positivo" },
  data_initiative: { texto: "Iniciativa de dados", tipo: "positivo" },
  security_compliance: { texto: "Exigência regulatória", tipo: "positivo" },
  cloud_migration: { texto: "Migração para nuvem", tipo: "neutro" },
  digital_transformation: { texto: "Transformação digital", tipo: "neutro" },
  crm_sales_initiative: { texto: "Iniciativa comercial", tipo: "neutro" },
  leadership_hire: { texto: "Nova liderança", tipo: "reativo" },
  cost_optimization: { texto: "Corte de custos", tipo: "reativo" },
};

const COR_SINAL = {
  positivo: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  neutro: "bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200",
  reativo: "bg-orange-50 text-laranja-escuro dark:bg-laranja/15 dark:text-laranja-claro",
};

const numero = new Intl.NumberFormat("pt-BR");
const dataHora = (iso: string) =>
  new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

function sinalDeAgora(c: Conta): Sinal | undefined {
  return [...c.signals].sort((a, b) => b.date.localeCompare(a.date))[0];
}

function EtiquetaSinal({ sinal }: { sinal: Sinal }) {
  const s = SINAIS[sinal.type] ?? { texto: sinal.type, tipo: "neutro" as const };
  return (
    <span className={`inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${COR_SINAL[s.tipo]}`}>{s.texto}</span>
  );
}

function Bloco({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section>
      <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{titulo}</h4>
      <div className="mt-1 text-sm text-slate-800 dark:text-slate-100">{children}</div>
    </section>
  );
}

function Dossie({ conta, fechar }: { conta: Conta; fechar: () => void }) {
  return (
    <aside className="w-full max-w-md shrink-0 overflow-y-auto rounded-xl border border-slate-200 bg-white p-6 dark:border-white/10 dark:bg-grafite">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-titulo text-lg font-medium text-grafite dark:text-white">{conta.name}</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {conta.sector} · {numero.format(conta.employees)} funcionários · {conta.tier} · score {conta.gtm_score}
          </p>
        </div>
        <button onClick={fechar} className="text-sm text-slate-500 hover:text-grafite dark:hover:text-white" aria-label="Fechar dossiê">
          Fechar
        </button>
      </div>
      <div className="mt-6 space-y-5">
        <Bloco titulo="Por que agora">{conta.dossier.why_now}</Bloco>
        <Bloco titulo="Por que a Jump">{conta.dossier.why_us}</Bloco>
        <Bloco titulo="Abordagem sugerida">{conta.dossier.suggested_approach}</Bloco>
        <Bloco titulo="Oferta recomendada">
          <span className="font-medium text-laranja-escuro dark:text-laranja-claro">{conta.dossier.recommended_offer}</span>
        </Bloco>
        <Bloco titulo="Decisores mapeados">
          <ul className="space-y-1">
            {conta.decision_makers.map((d) => (
              <li key={d.role}>
                {d.role} <span className="text-slate-500 dark:text-slate-400">· {d.area}</span>
                {d.is_decision_maker && (
                  <span className="ml-2 rounded bg-grafite px-1.5 py-0.5 text-[10px] font-medium uppercase text-white dark:bg-white dark:text-grafite">
                    decide
                  </span>
                )}
              </li>
            ))}
          </ul>
        </Bloco>
        <Bloco titulo="Sinais">
          {conta.signals.length === 0 ? (
            <span className="text-slate-500 dark:text-slate-400">Nenhum sinal ativo.</span>
          ) : (
            <ul className="space-y-2">
              {conta.signals.map((s) => (
                <li key={s.type + s.date}>
                  <EtiquetaSinal sinal={s} />
                  <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">
                    {new Date(s.date + "T12:00:00").toLocaleDateString("pt-BR")}
                  </span>
                  <div className="mt-0.5">{s.detail}</div>
                </li>
              ))}
            </ul>
          )}
        </Bloco>
        <Bloco titulo="Riscos">
          <ul className="list-disc pl-4">
            {conta.dossier.risks.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </Bloco>
      </div>
    </aside>
  );
}

export default function Contas() {
  const [dados, setDados] = useState<Resposta | null>(null);
  const [erro, setErro] = useState("");
  const [aberta, setAberta] = useState<Conta | null>(null);
  const [validando, setValidando] = useState(false);

  const carregar = () =>
    fetch("/api/contas")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setDados)
      .catch(() => setErro("Não foi possível carregar as contas."));

  useEffect(() => {
    carregar();
  }, []);

  async function validar() {
    setValidando(true);
    setErro("");
    const r = await fetch("/api/contas/validar", { method: "POST" });
    if (!r.ok) setErro((await r.json().catch(() => null))?.detail ?? "Não foi possível validar a lista.");
    await carregar();
    setValidando(false);
  }

  if (!dados) return <p className="text-sm text-slate-500">{erro || "Carregando contas..."}</p>;

  return (
    <div>
      {dados.simulacao && (
        <div className="mb-6 rounded-lg border border-laranja-claro bg-orange-50 px-4 py-3 text-sm text-grafite dark:border-laranja/40 dark:bg-laranja/10 dark:text-slate-100">
          <strong>Modo simulação:</strong> contas fictícias para o piloto do OPT-3. Os dados reais entram quando a
          integração com o ICP Jump for liberada.
        </div>
      )}

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-titulo text-2xl font-medium text-grafite dark:text-white">Contas</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            OPT-3 · lista da semana {dados.semana} · ordenada pelo GTM Score
          </p>
        </div>
        {dados.validacao ? (
          <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300">
            Lista validada por {dados.validacao.validated_by} em {dataHora(dados.validacao.validated_at)}
          </p>
        ) : (
          <button
            onClick={validar}
            disabled={validando}
            className="rounded-md bg-laranja px-4 py-2 text-sm font-medium text-white hover:bg-laranja-escuro disabled:opacity-60"
          >
            {validando ? "Validando..." : "Validar lista da semana"}
          </button>
        )}
      </div>
      {erro && <p className="mt-3 text-sm text-red-600 dark:text-red-300">{erro}</p>}

      <div className="mt-6 flex items-start gap-6">
        <div className="min-w-0 flex-1 overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-white/10 dark:bg-grafite">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-white/10 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Conta</th>
                <th className="px-4 py-3 font-medium">Porte</th>
                <th className="px-4 py-3 font-medium">Score</th>
                <th className="px-4 py-3 font-medium">Tier</th>
                <th className="px-4 py-3 font-medium">Sinal de agora</th>
              </tr>
            </thead>
            <tbody>
              {dados.contas.map((c) => {
                const sinal = sinalDeAgora(c);
                const ativa = aberta?.external_id === c.external_id;
                return (
                  <tr
                    key={c.external_id}
                    onClick={() => setAberta(c)}
                    className={`cursor-pointer border-b border-slate-100 last:border-0 dark:border-white/5 ${
                      ativa ? "bg-orange-50 dark:bg-laranja/10" : "hover:bg-slate-50 dark:hover:bg-white/5"
                    }`}
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-grafite dark:text-white">{c.name}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">{c.sector}</div>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-slate-700 dark:text-slate-200">{numero.format(c.employees)} func.</td>
                    <td className="px-4 py-3 font-titulo text-base font-medium text-grafite dark:text-white">{c.gtm_score}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-slate-700 dark:text-slate-200">{c.tier}</td>
                    <td className="px-4 py-3">
                      {sinal ? <EtiquetaSinal sinal={sinal} /> : <span className="text-xs text-slate-400">sem sinal</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {aberta && <Dossie conta={aberta} fechar={() => setAberta(null)} />}
      </div>
    </div>
  );
}
