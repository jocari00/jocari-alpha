// @ts-check
import { defineConfig } from "astro/config";

// GitHub Pages project site by default; set SITE_URL and BASE_PATH="/" for a custom domain.
export default defineConfig({
  site: process.env.SITE_URL ?? "https://jocari00.github.io",
  base: process.env.BASE_PATH ?? "/jocari-alpha",
  trailingSlash: "always",
  // Inline all CSS into each page. GitHub Pages lets browsers cache HTML for 10 minutes while
  // every deploy replaces the hashed stylesheet; a cached page could then ask for a stylesheet
  // that no longer exists and render unstyled. With inlined CSS a page always has its styles.
  build: { inlineStylesheets: "always" },
});
