export type Tema = "claro" | "escuro";

const CHAVE = "tema";

export function temaInicial(): Tema {
  try {
    const salvo = localStorage.getItem(CHAVE);
    if (salvo === "claro" || salvo === "escuro") return salvo;
  } catch {
    // sem acesso ao armazenamento: segue o sistema
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
}

export function aplicarTema(tema: Tema, salvar = false) {
  document.documentElement.classList.toggle("dark", tema === "escuro");
  if (salvar) {
    try {
      localStorage.setItem(CHAVE, tema);
    } catch {
      // sem acesso ao armazenamento: vale só nesta visita
    }
  }
}
