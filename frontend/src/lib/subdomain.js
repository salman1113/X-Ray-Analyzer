/**
 * Multi-tenant subdomain helpers.
 *
 * In dev:  abc.localhost:5173  → subdomain = "abc"
 * In prod: abc.domain.com     → subdomain = "abc"
 */

const BASE_DOMAIN = (import.meta.env.VITE_BASE_DOMAIN || "localhost")
  .toLowerCase()
  .trim();

const RESERVED = new Set([
  "www", "api", "app", "admin", "dashboard", "mail", "smtp", "ftp",
  "blog", "docs", "help", "support", "status", "assets", "static",
  "cdn", "auth", "login", "signup", "register", "public", "health",
]);

const SUBDOMAIN_RE = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/;

export function getBaseDomain() {
  return BASE_DOMAIN;
}

/**
 * Parse the current window's hostname and return the tenant subdomain,
 * or null if on the apex / reserved / not under BASE_DOMAIN.
 */
export function getCurrentSubdomain() {
  if (typeof window === "undefined") return null;
  return parseSubdomain(window.location.hostname);
}

export function parseSubdomain(hostname) {
  if (!hostname) return null;
  const host = hostname.toLowerCase();
  if (host === BASE_DOMAIN) return null;
  const suffix = `.${BASE_DOMAIN}`;
  if (!host.endsWith(suffix)) return null;
  const candidate = host.slice(0, -suffix.length);
  if (!candidate || candidate.includes(".")) return null;
  if (RESERVED.has(candidate)) return null;
  if (!SUBDOMAIN_RE.test(candidate)) return null;
  return candidate;
}

/**
 * Build a fully-qualified tenant URL. Returns "" if subdomain is invalid.
 */
export function buildTenantUrl(subdomain, path = "/") {
  if (!subdomain || !SUBDOMAIN_RE.test(subdomain)) return "";
  if (typeof window === "undefined") return "";
  const { protocol, port } = window.location;
  const host = port
    ? `${subdomain}.${BASE_DOMAIN}:${port}`
    : `${subdomain}.${BASE_DOMAIN}`;
  return `${protocol}//${host}${path}`;
}

/**
 * Validate that a URL is under our BASE_DOMAIN (prevents open redirect).
 */
export function isTrustedTenantUrl(url) {
  if (!url) return false;
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.toLowerCase();
    return host === BASE_DOMAIN || host.endsWith(`.${BASE_DOMAIN}`);
  } catch {
    return false;
  }
}

/** Are we on a tenant subdomain right now? */
export function isOnTenantSubdomain() {
  return getCurrentSubdomain() !== null;
}
