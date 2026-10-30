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

/** Composition by block (target weights; weights are static). */
export function composition(portfolio, instruments) {
  const byBlock = {};
  for (const [isin, w] of Object.entries(portfolio.weights)) {
    const f = instruments.funds[isin];
    (byBlock[f.block] ??= { block: f.block, label: instruments.blocks[f.block].label,
                            asset_class: f.asset_class, weight: 0, funds: [] });
    byBlock[f.block].weight += w;
    byBlock[f.block].funds.push({ isin, name: f.name, share_class: f.share_class, weight: w });
  }
  const order = Object.keys(instruments.blocks);
  return Object.values(byBlock).sort((a, b) => order.indexOf(a.block) - order.indexOf(b.block));
}
