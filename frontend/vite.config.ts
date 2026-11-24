import { createHash, createHmac } from "node:crypto";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";


const DOMAIN_KEYWORDS = [
  "secure", "portal", "verify", "account", "document", "session",
  "access", "cloud", "service", "gateway", "connect", "shield",
  "trust", "checkpoint", "identity", "docview", "signin", "auth",
];
const CONSONANTS = "bcdfghjklmnpqrstvwxyz";
const VOWELS = "aeiou";

function routePrefix(seed: string): string {
  const routeSeed = createHmac("sha256", seed).update("route").digest("hex");
  return createHash("sha256").update(routeSeed).digest("hex").slice(0, 12);
}

function localDomain(seed: string, style: string): string | undefined {
  if (style === "off") return undefined;
  if (style === "hash") {
    return `${createHash("sha256").update(`${seed}:domain-hash`).digest("hex").slice(0, 12)}.com`;
  }
  const purpose = style === "pronounceable" ? "domain-pronounceable" : "domain-keyword";
  const digest = createHash("sha256").update(`${seed}:${purpose}`).digest();
  if (style === "pronounceable") {
    const label = Array.from({ length: 9 }, (_, index) => {
      const pool = index % 2 === 0 ? CONSONANTS : VOWELS;
      return pool[digest[index] % pool.length];
    }).join("");
    return `${label}.com`;
  }
  if (style === "keyword") {
    const first = DOMAIN_KEYWORDS[digest[0] % DOMAIN_KEYWORDS.length];
    const remaining = DOMAIN_KEYWORDS.filter((word) => word !== first);
    return `${first}-${remaining[digest[1] % remaining.length]}.com`;
  }
  throw new Error(`Unsupported PHISHGATE_DOMAIN_STYLE: ${style}`);
}

// Optional: when PHISHGATE_DOMAIN_STYLE is not "off", the browser reaches
// this dev server through a fake local domain (see .env.example) instead of
// 127.0.0.1. Vite's dev server rejects any Host header it doesn't recognize
// by default (DNS-rebinding protection), so that domain must be allowlisted
// explicitly or every request would get a 403 "Blocked request".
const backendUrl = process.env.VITE_PHISHGATE_BACKEND_URL || "http://backend:8000";

// The Gate Host page lives at the bare prefix (e.g. /0087de010475/) instead of
// a nested /ui/ path — a literal "ui" segment reads as a dev-tool artifact,
// not a plausible real-site path (see "Detector-Blind Gate Routing" in
// README.md). /health and /api/* under the same prefix are proxied to the
// backend below, so only the exact bare route is reserved for the SPA.
export default defineConfig(({ command }) => {
  const seed = process.env.PHISHGATE_SEED?.trim();
  if (command === "serve" && !seed) {
    throw new Error("PHISHGATE_SEED must be set before starting Vite.");
  }
  const style = process.env.PHISHGATE_DOMAIN_STYLE?.trim() || "off";
  const derivedDomain = seed ? localDomain(seed, style) : undefined;
  const gateRoute = seed ? `/${routePrefix(seed)}/` : "/";
  return {
  // The production build uses relative asset URLs, so the same image can be
  // served below whichever seed-derived prefix Nginx computes at startup.
  // The Vite dev server proxies dynamically below instead, so it keeps the
  // default root base — setting it here too would make Vite refuse any
  // request outside {prefix}/, including the opaque per-kit access slugs.
  base: command === "build" ? "./" : "/",
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,
    allowedHosts: derivedDomain ? [derivedDomain] : undefined,
    proxy: {
      // Kits are reachable through the direct /kitN/ path or an opaque,
      // seed-derived access slug (see "Detector-Blind Gate Routing" in
      // README.md); since slugs are unpredictable, forward anything that
      // isn't the root placeholder, the Gate Host's own bare route, or
      // Vite's internal/module paths to the backend, which resolves the
      // rest (including /{prefix}/health and /{prefix}/api/*).
      // Vite matches this pattern against the full request URL, query string
      // included, so the gate route's own `?t=...` token must not defeat the
      // exclusion below.
      [`^(?!/(?:\\?|$))(?!${gateRoute}(?:\\?|$))(?!/@)(?!/src/)(?!/node_modules/).+$`]: {
        target: backendUrl,
        changeOrigin: true,
      },
    },
  },
  };
});
