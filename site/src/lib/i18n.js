// Interface strings, number/date formatting and localized paths.
export const LANGS = ["en", "es"];
export const LOCALE = { en: "en-GB", es: "es-ES" };

export const T = {
  en: {
    tagline: "Model portfolios & market commentary",
    description: "Five model portfolios, from all bonds to all equity, each measured every month against a passive benchmark. Decisions are recorded publicly before they take effect.",
    nav: { home: "Home", portfolios: "Portfolios", commentary: "Market commentary",
           methodology: "Methodology", about: "About", legal: "Legal" },
    switchTo: "Español", switchLabel: "Ver en español",
    theme: "Toggle light/dark theme",
    footer: "Model portfolios for educational and illustrative purposes only. Not investment advice or a personalised recommendation. No third-party money is managed. Past performance does not guarantee future returns. Figures before 30 Oct 2026 are estimated.",
    fullLegal: "Full legal notice",
    pending: "Tracking starts on 30 October 2026. The first figures (the estimated year to date, then each month end) are published after that close is calculated.",
    equity: "Equity", fixedIncome: "Fixed income",
    portfolio: "Portfolio", benchmark: "Benchmark", difference: "Difference",
    ytd: "YTD", sinceStart: "Since 31 Dec 2025", lastPeriod: "Last period",
    estimated: "Estimated", live: "Live",
    estimatedNote: (from, to) => `Estimated: ${from} – ${to}, with the current target weights. Live monthly tracking from ${to}.`,
    chartTitle: "Growth of 100 vs benchmark",
    range: { ytd: "YTD", "1y": "1Y", all: "All" },
    dataTable: "Show data table", date: "Date",
    composition: "Composition", byBlock: "By block", byFund: "By fund", weight: "Target weight",
    staticWeights: "Weights are static: the portfolio is reset to these targets at every month end.",
    benchmarkMix: "Benchmark mix",
    commentary: "Commentary", comingSoon: "Commentary coming soon.",
    portfolioComment: "About this portfolio", blockComment: "Why each block", fundComment: "Each fund's role",
    latestCommentary: "Latest market commentary", allCommentary: "All commentary",
    written: "Written", period: "Period", monthReturns: "Returns for the month", ytdTo: "Year to date to",
    onlyIn: (l) => `This commentary is only available in ${l === "es" ? "Spanish" : "English"}.`,
    ladder: "Risk ladder", ladderNote: "Each profile is described in general terms. None of them is a recommendation for any particular person.",
    profiles: "The five profiles", notValued: "First figures after the October close",
    inquiries: "For professional inquiries",
  },
  es: {
    tagline: "Carteras modelo y comentario de mercado",
    description: "Cinco carteras modelo, de todo bonos a todo bolsa, medidas cada mes frente a un benchmark pasivo. Las decisiones se registran públicamente antes de entrar en vigor.",
    nav: { home: "Inicio", portfolios: "Carteras", commentary: "Comentario de mercado",
           methodology: "Metodología", about: "Sobre mí", legal: "Aviso legal" },
    switchTo: "English", switchLabel: "View in English",
    theme: "Cambiar tema claro/oscuro",
    footer: "Carteras modelo con fines exclusivamente educativos e ilustrativos. No constituye asesoramiento ni recomendación personalizada. No se gestiona dinero de terceros. Las rentabilidades pasadas no garantizan rentabilidades futuras. Las cifras anteriores al 30 oct 2026 son estimadas.",
    fullLegal: "Aviso legal completo",
    pending: "El seguimiento empieza el 30 de octubre de 2026. Las primeras cifras (el año estimado y después cada fin de mes) se publican cuando se calcule ese cierre.",
    equity: "Renta variable", fixedIncome: "Renta fija",
    portfolio: "Cartera", benchmark: "Benchmark", difference: "Diferencia",
    ytd: "En el año", sinceStart: "Desde el 31 dic 2025", lastPeriod: "Último periodo",
    estimated: "Estimado", live: "Live",
    estimatedNote: (from, to) => `Estimado: ${from} – ${to}, con los pesos objetivo actuales. Seguimiento mensual live desde el ${to}.`,
    chartTitle: "Evolución de 100 frente al benchmark",
    range: { ytd: "Año", "1y": "1A", all: "Todo" },
    dataTable: "Ver tabla de datos", date: "Fecha",
    composition: "Composición", byBlock: "Por bloque", byFund: "Por fondo", weight: "Peso objetivo",
    staticWeights: "Los pesos son estáticos: la cartera vuelve a estos objetivos a cada fin de mes.",
    benchmarkMix: "Composición del benchmark",
    commentary: "Comentario", comingSoon: "Comentario próximamente.",
    portfolioComment: "Sobre esta cartera", blockComment: "Por qué cada bloque", fundComment: "El papel de cada fondo",
    latestCommentary: "Último comentario de mercado", allCommentary: "Todos los comentarios",
    written: "Escrito", period: "Periodo", monthReturns: "Rentabilidades del mes", ytdTo: "En el año, a",
    onlyIn: (l) => `Este comentario solo está disponible en ${l === "es" ? "español" : "inglés"}.`,
    ladder: "Escalera de riesgo", ladderNote: "Cada perfil se describe de forma general. Ninguno es una recomendación para una persona concreta.",
    profiles: "Los cinco perfiles", notValued: "Primeras cifras tras el cierre de octubre",
    inquiries: "For professional inquiries",
  },
};

export const BLOCK_LABELS = {
  es: {
    liquidity_short_term: "Liquidez y renta fija a corto plazo",
    credit_flexible: "Crédito y renta fija flexible",
    defensive_alternatives: "Alternativos defensivos",
    aggressive_alternatives: "Alternativos agresivos",
    equity: "Renta variable",
    equity_index: "Renta variable global (indexada)",
    equity_value: "Renta variable value",
    equity_emerging: "Renta variable emergente",
    equity_technology: "Renta variable tecnológica",
  },
};

export const blockLabel = (lang, block, fallback) => BLOCK_LABELS[lang]?.[block] ?? fallback;

/** Localized URL under the site base. path like "portfolios/balanced/". */
export function href(lang, path = "") {
  const base = import.meta.env.BASE_URL.replace(/\/?$/, "/");
  return base + (lang === "es" ? "es/" : "") + path;
}

// Typographic minus sign (U+2212) for negative figures.
const minus = (s) => s.replace("-", "\u2212");

export const pct = (lang, x, signed = true) =>
  x == null ? "–" : minus(new Intl.NumberFormat(LOCALE[lang], {
    style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2,
    signDisplay: signed ? "exceptZero" : "auto" }).format(x));

// A difference between two returns, in percentage points.
export const pp = (lang, x) =>
  x == null ? "–" : minus(new Intl.NumberFormat(LOCALE[lang], {
    minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: "exceptZero" }).format(x * 100))
    + (lang === "en" ? "\u00a0pp" : "\u00a0p.\u00a0p.");

export const num = (lang, x, d = 2) =>
  minus(new Intl.NumberFormat(LOCALE[lang], { minimumFractionDigits: d, maximumFractionDigits: d }).format(x));

export const weight = (lang, w) =>
  new Intl.NumberFormat(LOCALE[lang], { maximumFractionDigits: 1 }).format(w) + " %";

export const fmtDate = (lang, iso, opts = { day: "numeric", month: "short", year: "numeric" }) =>
  iso ? new Intl.DateTimeFormat(LOCALE[lang], { ...opts, timeZone: "UTC" }).format(new Date(iso + "T00:00:00Z")) : "";

export const fmtPeriod = (lang, period) => {
  // "2026-Q1" or "2026-10"
  const q = /^(\d{4})-Q([1-4])$/.exec(period);
  if (q) return lang === "es" ? `${q[2]}.º trimestre ${q[1]}` : `Q${q[2]} ${q[1]}`;
  const m = /^(\d{4})-(\d{2})$/.exec(period);
  if (m) {
    const s = fmtDate(lang, `${period}-01`, { month: "long", year: "numeric" });
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  return period;
};
