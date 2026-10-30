// Editorial content (Markdown files under site/content/), resolved per language.
const commentary = import.meta.glob("../../content/commentary/*/*.md", { eager: true });
const pages = import.meta.glob("../../content/pages/*.md", { eager: true });
const editorial = import.meta.glob("../../content/editorial/*.md", { eager: true });

const isFilled = (mod) => (mod.rawContent?.() ?? "").trim().length > 0;

function sortKey(period) {
  const q = /^(\d{4})-Q([1-4])$/.exec(period);
  return q ? `${q[1]}-${String(q[2] * 3).padStart(2, "0")}-q` : `${period}-m`;
}

/** All commentaries for a language, newest period first. Falls back to the other language. */
export function listCommentary(lang) {
  const bySlug = {};
  for (const [file, mod] of Object.entries(commentary)) {
    const m = /commentary\/(en|es)\/([^/]+)\.md$/.exec(file);
    if (!m) continue;
    (bySlug[m[2]] ??= {})[m[1]] = mod;
  }
  return Object.entries(bySlug).map(([slug, v]) => {
    const other = lang === "en" ? "es" : "en";
    let mod = v[lang], shownLang = lang;
    if ((!mod || !isFilled(mod)) && v[other] && isFilled(v[other])) { mod = v[other]; shownLang = other; }
    mod ??= v[other];
    const fm = mod.frontmatter;
    const plain = (mod.rawContent?.() ?? "").replace(/[#>*_`\[\]()!-]/g, " ").replace(/\s+/g, " ").trim();
    const excerpt = plain.length > 220 ? plain.slice(0, 220).replace(/\s\S*$/, "") + "…" : plain;
    return { slug, period: String(fm.period), kind: fm.kind, title: fm.title || "", written: fm.written ? String(fm.written).slice(0, 10) : null,
             portfolios: fm.portfolios || {}, filled: isFilled(mod), Content: mod.Content, excerpt,
             shownLang, fallback: shownLang !== lang };
  }).sort((a, b) => sortKey(b.period).localeCompare(sortKey(a.period)));
}

export function getPage(name, lang) {
  const mod = pages[`../../content/pages/${name}.${lang}.md`];
  return { title: mod.frontmatter.title, frontmatter: mod.frontmatter, Content: mod.Content };
}

export function getEditorial(lang) {
  return editorial[`../../content/editorial/${lang}.md`].frontmatter;
}
