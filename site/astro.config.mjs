// @ts-check
import { defineConfig } from "astro/config";

// GitHub Pages project site by default; set SITE_URL and BASE_PATH="/" for a custom domain.
export default defineConfig({
  site: process.env.SITE_URL ?? "https://jocari00.github.io",
  base: process.env.BASE_PATH ?? "/jocari-alpha",
  trailingSlash: "always",
});
