// =============================================================================
// SHARED UTILITY FUNCTIONS
// =============================================================================

/**
 * Extract subdomain from host string
 * Works for both server and client
 */
export function extractSubdomain(host: string): string | null {
  if (!host) return null;

  // Remove port if present
  const [hostWithoutPort] = host.split(":");
  const parts = hostWithoutPort.split(".");

  // Handle different scenarios:
  // localhost -> null
  // domain.com -> null
  // subdomain.domain.com -> subdomain
  // sub1.sub2.domain.com -> sub1
  // www.domain.com -> null (treat www as special case, not subdomain)
  console.log(hostWithoutPort, parts);

  // Handle localhost development environment
  if (
    hostWithoutPort === "localhost" ||
    hostWithoutPort.endsWith(".localhost")
  ) {
    return parts.length > 0 ? parts[0] : null;
  }

  // Handle production domains
  if (parts.length <= 2) {
    return null; // No subdomain (domain.com, example.org)
  }

  const potentialSubdomain = parts[0];

  // Treat 'www' as not a subdomain
  if (potentialSubdomain === "www") {
    return null;
  }

  return potentialSubdomain;
}

/**
 * Extract main domain from host string
 */
export function extractMainDomain(host: string): string | null {
  if (!host) return null;

  const [hostWithoutPort] = host.split(":");
  const parts = hostWithoutPort.split(".");

  if (parts.length < 2) {
    return hostWithoutPort; // localhost case
  }

  // Return last two parts as main domain
  return parts.slice(-2).join(".");
}

/**
 * Validate if a string is a valid subdomain
 */
export function isValidSubdomain(subdomain: string): boolean {
  if (!subdomain || typeof subdomain !== "string") {
    return false;
  }

  // Basic subdomain validation rules
  const subdomainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/;

  return (
    subdomainRegex.test(subdomain) &&
    subdomain.length <= 63 &&
    !subdomain.startsWith("-") &&
    !subdomain.endsWith("-")
  );
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

// =============================================================================
// CORE URL TRANSFORMATION FUNCTIONS
// =============================================================================

const BASE_DOMAIN = (process.env.BASE_DOMAIN || "").trim().toLowerCase();

/** Split host:port into [hostname, port?] */
function splitHostPort(host: string): [string, string?] {
  const idx = host.lastIndexOf(":");
  if (idx > -1 && !host.includes("]")) {
    // naive but OK for IPv4 + hostname:port; (IPv6 will be like [::1]:3000)
    const name = host.slice(0, idx);
    const port = host.slice(idx + 1);
    return [name, port];
  }
  return [host, undefined];
}

function isIPv6(host: string) {
  return host.startsWith("[") && host.endsWith("]");
}
function isIPv4(host: string) {
  return /^\d{1,3}(\.\d{1,3}){3}$/.test(host);
}
function isIp(host: string) {
  return isIPv4(host) || isIPv6(host);
}

function isLocalhostLike(hostname: string) {
  return (
    hostname === "localhost" ||
    hostname.endsWith(".localhost") ||
    hostname === "[::1]" ||
    hostname === "127.0.0.1" ||
    hostname === "0.0.0.0"
  );
}

function removeLeadingWww(label: string) {
  return label.startsWith("www.") ? label.slice(4) : label;
}

/**
 * Canonicalize a host (with optional port) based on rules:
 * - localhost & IP: strip subdomain (result 'localhost[:port]' or IP)
 * - vercel baseDomain: force exactly baseDomain (strip any subdomains)
 * - custom baseDomain: if subdomain present and not 'www', replace with 'www'
 * - otherwise: leave untouched
 */
export function canonicalizeHost(
  hostWithPort: string,
  baseDomain: string = BASE_DOMAIN
): { host: string; changed: boolean } {
  if (!hostWithPort) return { host: hostWithPort, changed: false };

  // Separate host/port
  let host = hostWithPort;
  let port: string | undefined;
  if (!isIPv6(hostWithPort)) {
    [host, port] = splitHostPort(hostWithPort);
  }

  const original = hostWithPort;
  let changed = false;

  // IPv6 with port like [::1]:3000
  if (isIPv6(host)) {
    // Treat ::1 like localhost style (no subdomain logic needed)
    return { host: original, changed: false };
  }

  const hostname = host.toLowerCase();

  // Local dev / IPs: strip any subdomain, never add www
  if (isLocalhostLike(hostname) || isIp(hostname)) {
    const canonical =
      hostname === "localhost" || isIp(hostname) ? hostname : "localhost";
    const result = port ? `${canonical}:${port}` : canonical;
    changed = result !== original;
    return { host: result, changed };
  }

  if (baseDomain) {
    const bd = baseDomain.toLowerCase();
    const isVercelBase = bd.endsWith(".vercel.app");

    if (hostname === bd) {
      // Already canonical for base domain
      const result = port ? `${hostname}:${port}` : hostname;
      changed = result !== original;
      return { host: result, changed };
    }

    if (hostname.endsWith("." + bd)) {
      // Has some subdomain on the baseDomain
      if (isVercelBase) {
        // Vercel: force exactly baseDomain (strip ANY subdomain, including 'www')
        const result = port ? `${bd}:${port}` : bd;
        changed = result !== original;
        return { host: result, changed };
      } else {
        // Custom domain: replace any subdomain with 'www'
        const result = port ? `www.${bd}:${port}` : `www.${bd}`;
        changed = result !== original;
        return { host: result, changed };
      }
    }
  }

  // Not localhost, not IP, no baseDomain match -> leave as-is
  return { host: original, changed: false };
}

/** Canonicalize a full URL string (maintains protocol/path/query/hash). */
export function canonicalizeUrl(inputUrl: string): {
  url: string;
  changed: boolean;
} {
  const u = new URL(inputUrl);
  const { host, changed } = canonicalizeHost(u.host);
  if (changed) {
    u.host = host;
  }
  return { url: u.toString(), changed };
}

/**
 * Remove subdomain from a URL and add www prefix
 * Works with full URLs or host strings
 */
export function removeSubdomainAddWww(
  url: string,
  preservePath: boolean = true
): string {
  try {
    let urlObj: URL;
    const originalUrl = url;

    // Handle both full URLs and host-only strings
    if (url.startsWith("http://") || url.startsWith("https://")) {
      urlObj = new URL(url);
    } else {
      // Assume it's a host string, add protocol
      urlObj = new URL(`https://${url}`);
    }

    // Save original path and search params
    const { pathname, search, hash } = urlObj;

    const host = urlObj.host;
    const [hostWithoutPort, port] = host.split(":");
    const parts = hostWithoutPort.split(".");

    let newHost: string;

    // Handle localhost specially
    if (
      hostWithoutPort === "localhost" ||
      hostWithoutPort.endsWith(".localhost")
    ) {
      newHost = `www.localhost${port ? ":" + port : ""}`;
    }
    // Handle regular domains
    else if (parts.length <= 2) {
      // No subdomain (domain.com) - just add www
      if (parts[0] === "www") {
        newHost = host; // Already has www
      } else {
        newHost = `www.${hostWithoutPort}${port ? ":" + port : ""}`;
      }
    } else {
      // Has subdomain - remove it and add www
      const mainDomain = parts.slice(-2).join(".");
      newHost = `www.${mainDomain}${port ? ":" + port : ""}`;
    }

    // Update the host
    urlObj.host = newHost;

    // Restore original path and search params if preservePath is true
    if (preservePath) {
      urlObj.pathname = pathname;
      urlObj.search = search;
      urlObj.hash = hash;
    } else {
      urlObj.pathname = "/";
      urlObj.search = "";
      urlObj.hash = "";
    }

    const result = urlObj.toString();
    console.log("Transformed URL:", { originalUrl, result, preservePath, url });
    return result;
  } catch (error) {
    console.error("Error removing subdomain and adding www:", error);
    return url; // Return original if error
  }
}

/**
 * Remove subdomain from host string only (no protocol)
 */
export function removeSubdomainFromHost(host: string): string {
  try {
    const [hostWithoutPort, port] = host.split(":");
    const parts = hostWithoutPort.split(".");

    if (parts.length <= 2) {
      // No subdomain - add www if not present
      if (parts[0] === "www") {
        return host;
      } else {
        return `www.${hostWithoutPort}${port ? ":" + port : ""}`;
      }
    } else {
      // Has subdomain - remove and add www
      const mainDomain = parts.slice(-2).join(".");
      return `www.${mainDomain}${port ? ":" + port : ""}`;
    }
  } catch (error) {
    console.error("Error removing subdomain from host:", error);
    return host;
  }
}

/**
 * Check if current environment has a subdomain
 */
export function hasSubdomain(host?: string): boolean {
  if (typeof window !== "undefined") {
    host = host || window.location.host;
  }

  if (!host) return false;

  const [hostWithoutPort] = host.split(":");
  const parts = hostWithoutPort.split(".");

  return parts.length > 2 && parts[0] !== "www";
}

/**
 * Generate www URL from any URL
 */
export function toWwwUrl(url: string, preservePath: boolean = true): string {
  return removeSubdomainAddWww(url, preservePath);
}

/**
 * Generate www host from any host
 */
export function toWwwHost(host: string): string {
  return removeSubdomainFromHost(host);
}
