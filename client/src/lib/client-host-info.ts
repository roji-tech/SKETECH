// =============================================================================
// CLIENT-SIDE SUBDOMAIN FUNCTION (use in Client Components)
// =============================================================================

"use client";

import {
  extractSubdomain,
  extractMainDomain,
  removeSubdomainAddWww,
  removeSubdomainFromHost,
} from "@/utils/hostInfoUtils";

/**
 * Client-side function to extract subdomain from window.location
 * Use this in Client Components or browser-side code
 */
export function getSubdomainClient(): string | null {
  // Check if we're in a browser environment
  if (typeof window === "undefined") {
    console.warn("getSubdomainClient called on server-side");
    return null;
  }

  try {
    const host = window.location.host;
    return extractSubdomain(host);
  } catch (error) {
    console.error("Error getting subdomain on client:", error);
    return null;
  }
}

/**
 * Client-side function to get full host information
 */
export function getHostInfoClient(): {
  host: string | null;
  subdomain: string | null;
  domain: string | null;
  port: string | null;
  protocol: string | null;
  fullUrl: string | null;
} {
  if (typeof window === "undefined") {
    return {
      host: null,
      subdomain: null,
      domain: null,
      port: null,
      protocol: null,
      fullUrl: null,
    };
  }

  try {
    const location = window.location;
    const host = location.host;
    const [hostWithoutPort, port] = host.split(":");
    const subdomain = extractSubdomain(host);
    const domain = extractMainDomain(host);

    return {
      host,
      subdomain,
      domain,
      port: port || null,
      protocol: location.protocol,
      fullUrl: location.href,
    };
  } catch (error) {
    console.error("Error getting host info on client:", error);
    return {
      host: null,
      subdomain: null,
      domain: null,
      port: null,
      protocol: null,
      fullUrl: null,
    };
  }
}

// =============================================================================
// CLIENT-SIDE FUNCTIONS
// =============================================================================

/**
 * Client-side function to get current URL without subdomain + www
 */
export function getWwwUrlClient(preservePath: boolean = true): string | null {
  if (typeof window === "undefined") {
    console.warn("getWwwUrlClient called on server-side");
    return null;
  }

  try {
    const currentUrl = preservePath
      ? window.location.href
      : window.location.origin;
    return removeSubdomainAddWww(currentUrl, preservePath);
  } catch (error) {
    console.error("Error getting www URL on client:", error);
    return null;
  }
}

/**
 * Client-side function to redirect to www version
 */
export function redirectToWwwClient(preservePath: boolean = true): void {
  if (typeof window === "undefined") {
    console.warn("redirectToWwwClient called on server-side");
    return;
  }

  const wwwUrl = getWwwUrlClient(preservePath);

  if (wwwUrl && wwwUrl !== window.location.href) {
    window.location.href = wwwUrl;
  }
}

/**
 * Client-side function to get www host only
 */
export function getWwwHostClient(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return removeSubdomainFromHost(window.location.host);
  } catch (error) {
    console.error("Error getting www host on client:", error);
    return null;
  }
}
