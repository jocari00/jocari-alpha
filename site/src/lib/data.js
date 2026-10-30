// Build-time data: decisions, instruments and computed results from the repository root.
import fs from "node:fs";
import path from "node:path";
import { load as loadYaml } from "js-yaml";

const ROOT = path.resolve(process.cwd(), "..");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

export const PORTFOLIO_IDS = ["defensive", "conservative", "balanced", "dynamic", "aggressive"];

export function loadInstruments() {
  const cfg = loadYaml(read("config/instruments.yaml"));
  const blocks = loadYaml(read("config/blocks.yaml"));
  const funds = Object.fromEntries(cfg.funds.map((f) => [f.isin, { ...f, asset_class: blocks[f.block].asset_class }]));
  const benchmarks = Object.fromEntries(cfg.benchmarks.map((b) => [b.isin, b]));
  return { funds, benchmarks, blocks };
}

export function loadPortfolios() {
  return PORTFOLIO_IDS.map((id) => {
    const p = loadYaml(read(`decisions/${id}.yaml`));
    const current = p.decisions[p.decisions.length - 1];
    return { id, name: p.name, equity: p.equity_target, fixedIncome: p.fixed_income_target,
             benchmark: p.benchmark, weights: current.weights };
  });
}

export function loadTracking() {
  return loadYaml(read("config/tracking.yaml"));
}

/** Results computed by `jocari compute`. Until they exist, no figures at all are shown
 *  (`pending: true`): the site never displays invented or sample returns. */
export function loadResults() {
  const real = path.join(ROOT, "data/results.json");
  if (fs.existsSync(real)) return { ...JSON.parse(fs.readFileSync(real, "utf8")), pending: false };
  const tr = loadTracking();
  const iso = (d) => (d instanceof Date ? d.toISOString().slice(0, 10) : String(d));
  return { base_date: iso(tr.base_date), live_start: iso(tr.live_start), portfolios: {}, pending: true };
}

/** Sections shown on the site: the four equity blocks form one "Equity" section. */
export const SECTIONS = [
  { id: "liquidity_short_term", blocks: ["liquidity_short_term"] },
  { id: "credit_flexible", blocks: ["credit_flexible"] },
  { id: "defensive_alternatives", blocks: ["defensive_alternatives"] },
  { id: "equity", blocks: ["equity_index", "equity_value", "equity_emerging", "equity_technology"] },
  { id: "aggressive_alternatives", blocks: ["aggressive_alternatives"] },
];
export const sectionOf = (block) => SECTIONS.find((s) => s.blocks.includes(block)).id;

export function sectionLabel(instruments, id) {
  return id === "equity" ? "Equity" : instruments.blocks[id].label;
}

/** Composition by section (target weights; weights are static). */
export function composition(portfolio, instruments) {
  const bySection = {};
  for (const [isin, w] of Object.entries(portfolio.weights)) {
    const f = instruments.funds[isin];
    const id = sectionOf(f.block);
    (bySection[id] ??= { block: id, label: sectionLabel(instruments, id), asset_class: f.asset_class, weight: 0, funds: [] });
    bySection[id].weight += w;
    bySection[id].funds.push({ isin, name: f.name, share_class: f.share_class, weight: w });
  }
  const order = SECTIONS.map((s) => s.id);
  return Object.values(bySection).sort((a, b) => order.indexOf(a.block) - order.indexOf(b.block));
}

/** Decision log across portfolios, newest first; identical entries on the same date are merged. */
export function loadDecisionLog() {
  const byKey = {};
  for (const id of PORTFOLIO_IDS) {
    const p = loadYaml(read(`decisions/${id}.yaml`));
    for (const d of p.decisions) {
      const date = d.effective_date instanceof Date ? d.effective_date.toISOString().slice(0, 10) : String(d.effective_date);
      const key = `${date}|${d.kind}`;
      (byKey[key] ??= { date, kind: d.kind, portfolios: [] }).portfolios.push(p.name);
    }
  }
  return Object.values(byKey).sort((a, b) => b.date.localeCompare(a.date));
}
