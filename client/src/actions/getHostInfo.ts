// =============================================================================
// SERVER-SIDE SUBDOMAIN FUNCTION (use in Server Components/Actions)
// =============================================================================

"use server";

import { cookies, headers } from "next/headers";
import {
  extractSubdomain,
  extractMainDomain,
  removeSubdomainAddWww,
  removeSubdomainFromHost,
  canonicalizeUrl,
} from "@/utils/hostInfoUtils";

/**
 * Server-side function to extract subdomain from request headers
 * Use this in Server Components, Server Actions, or API routes
 */
export async function getSubdomainServer(): Promise<string | null> {
  try {
    // If NO_SUBDOMAIN is set, try to get subdomain from cookies first
    if (process.env.NO_SUBDOMAIN) {
      const cookieStore = await cookies();
      console.log("Cookie Store:", process.env.NO_SUBDOMAIN, cookieStore);
      let subdomain = cookieStore?.get("school_subdomain")?.value || null;

      if (!subdomain && typeof window !== "undefined") {
        subdomain = sessionStorage.getItem("school_subdomain") || null;
      }

      if (subdomain) return subdomain;
    }

    const headersList = await headers();
    const host = headersList.get("host");

    console.log("Host:", host);

    if (!host) {
      console.warn("No host header found in request");
      return null;
    }

    return extractSubdomain(host);
  } catch (error) {
    console.warn(
      "Error getting subdomain on server:",
      error instanceof Error ? error.message : error
    );
    return null;
  }
}

/**
 * Server-side function to get full host information
 */
export async function getHostInfoInServer(): Promise<{
  host: string | null;
  subdomain: string | null;
  domain: string | null;
  port: string | null;
}> {
  try {
    const headersList = await headers();
    const host = headersList.get("host");

    if (!host) {
      return { host: null, subdomain: null, domain: null, port: null };
    }

    const [hostWithoutPort, port] = host.split(":");
    const subdomain = extractSubdomain(host);
    const domain = extractMainDomain(host);

    return {
      host,
      subdomain,
      domain,
      port: port || null,
    };
  } catch (error) {
    console.error("Error getting host info on server:", error);
    return { host: null, subdomain: null, domain: null, port: null };
  }
}

export async function getWWWUrl() {
  const subdomain = await getSubdomainServer();
  if (subdomain && subdomain !== "www") {
    return `https://${subdomain}.${window.location.host}`;
  }
}

/**
 * Server-safe helper: build current URL from headers and canonicalize it.
 * Accept optional pathname/search to avoid relying on custom headers.
 */
export async function getCanonicalUrlServer(opts?: {
  pathname?: string;
  search?: string;
}): Promise<{ url: string; changed: boolean } | null> {
  try {
    const h = await headers();
    const host = h.get("x-forwarded-host") || h.get("host"); // prefer forwarded host on proxies
    const proto = h.get("x-forwarded-proto") || "http";

    if (!host) return null;

    // If caller passes pathname/search (best on known routes like /register), use them.
    // Otherwise, fall back to root to avoid page-level loops.
    const pathname = opts?.pathname ?? "/";
    const search = opts?.search ?? "";

    const current = new URL(`${proto}://${host}${pathname}${search}`);
    return canonicalizeUrl(current.toString());
  } catch {
    return null;
  }
}

// =============================================================================
// USAGE EXAMPLES
// =============================================================================

/*
// SERVER COMPONENT USAGE
export default async function ServerComponent() {
  const subdomain = await getSubdomainServer()
  const hostInfo = await getHostInfoServer()
  
  return (
    <div>
      <h1>Current Subdomain: {subdomain || 'None'}</h1>
      <p>Host: {hostInfo.host}</p>
      <p>Domain: {hostInfo.domain}</p>
    </div>
  )
}

// CLIENT COMPONENT USAGE
'use client'
export default function ClientComponent() {
  const { subdomain, isLoading, hostInfo } = useSubdomain()
  
  if (isLoading) {
    return <div>Loading...</div>
  }
  
  return (
    <div>
      <h1>Current Subdomain: {subdomain || 'None'}</h1>
      <p>Host: {hostInfo.host}</p>
      <p>Full URL: {hostInfo.fullUrl}</p>
    </div>
  )
}

// DIRECT CLIENT USAGE
function handleButtonClick() {
  const subdomain = getSubdomainClient()
  const hostInfo = getHostInfoClient()
  
  console.log('Subdomain:', subdomain)
  console.log('Host Info:', hostInfo)
}

// SERVER ACTION USAGE
export async function myServerAction() {
  'use server'
  
  const subdomain = await getSubdomainServer()
  
  if (!subdomain) {
    throw new Error('No subdomain found')
  }
  
  // Use subdomain in your logic
  console.log(`Processing for school: ${subdomain}`)
}

// API ROUTE USAGE (app/api/example/route.ts)
import { getSubdomainServer } from '@/lib/subdomain-utils'

export async function GET() {
  const subdomain = await getSubdomainServer()
  
  return Response.json({
    subdomain,
    message: `Hello from ${subdomain || 'main'} domain`
  })
}
*/

// =============================================================================
// SUBDOMAIN REMOVAL AND WWW REDIRECT UTILITIES
// =============================================================================

import { redirect } from "next/navigation";
import { current } from "immer";

/**
 * Server-side function to get current URL without subdomain + www
 * Use in Server Components or Server Actions
 */
export async function getWwwUrlServer(options?: {
  preservePath?: boolean;
}): Promise<string | null> {
  try {
    const preservePath = options?.preservePath ?? true;
    const headersList = await headers();
    const host = headersList.get("host");
    const protocol = headersList.get("x-forwarded-proto") || "http";
    const pathname = headersList.get("x-pathname") || "/";
    const search = headersList.get("x-search") || "";

    if (!host) {
      console.warn("No host header found");
      return null;
    }

    // Construct the full current URL with path and search params
    const currentUrl = new URL(`${protocol}://${host}`);
    console.log(
      "Current URL:",
      currentUrl.toString(),
      pathname,
      search,
      preservePath
    );

    if (preservePath) {
      currentUrl.pathname = pathname;
      currentUrl.search = search;
    } else {
      currentUrl.pathname = "/";
      currentUrl.search = "";
    }

    // Process the URL to remove subdomain and add www
    const result = removeSubdomainAddWww(currentUrl.toString(), preservePath);
    console.log("Redirecting to:", result);
    return result;
  } catch (error) {
    console.error("Error getting www URL on server:", error);
    return null;
  }
}

/**
 * Server-side function to redirect to www version (removes subdomain)
 * Use in Server Components or middleware
 */
export async function redirectToWwwServer(options?: {
  preservePath?: boolean;
}): Promise<never> {
  const preservePath = options?.preservePath ?? true;
  const wwwUrl = await getWwwUrlServer({ preservePath });

  if (!wwwUrl) {
    throw new Error("Could not determine www URL for redirect");
  }

  redirect(wwwUrl);
}

/**
 * Server-side function to get www host only
 */
export async function getWwwHostServer(): Promise<string | null> {
  try {
    const headersList = await headers();
    const host = headersList.get("host");

    if (!host) {
      return null;
    }

    return removeSubdomainFromHost(host);
  } catch (error) {
    console.error("Error getting www host on server:", error);
    return null;
  }
}

// =============================================================================
// USAGE EXAMPLES
// =============================================================================

/*
// SERVER COMPONENT USAGE
export default async function ServerComponent() {
  const wwwUrl = await getWwwUrlServer()
  const wwwHost = await getWwwHostServer()
  
  // Conditional redirect
  const headersList = headers()
  const currentHost = headersList.get('host')
  
  if (hasSubdomain(currentHost)) {
    // Redirect users from subdomain to www
    await redirectToWwwServer()
  }
  
  return (
    <div>
      <p>WWW URL: {wwwUrl}</p>
      <p>WWW Host: {wwwHost}</p>
      <a href={wwwUrl}>Go to main site</a>
    </div>
  )
}

// CLIENT COMPONENT USAGE
'use client'
export default function ClientComponent() {
  const { wwwUrl, wwwHost, isSubdomain, isLoading, redirectToWww } = useWwwUrl()
  
  if (isLoading) {
    return <div>Loading...</div>
  }
  
  return (
    <div>
      <p>WWW URL: {wwwUrl}</p>
      <p>Has Subdomain: {isSubdomain}</p>
      
      {isSubdomain && (
        <button onClick={redirectToWww}>
          Go to Main Site (www)
        </button>
      )}
      
      <a href={wwwUrl}>Main Site Link</a>
    </div>
  )
}

// DIRECT USAGE EXAMPLES
const examples = {
  // Transform any URL
  'https://school1.example.com/dashboard' → 'https://www.example.com/dashboard',
  'https://app.mysite.com/login?redirect=home' → 'https://www.mysite.com/login?redirect=home',
  'http://sub.localhost:3000/api' → 'http://www.localhost:3000/api',
  'https://example.com' → 'https://www.example.com',
  'https://www.example.com' → 'https://www.example.com', // No change needed
  
  // Without preserving path
  'https://school1.example.com/dashboard' → 'https://www.example.com/' // (preservePath: false)
}

// API ROUTE USAGE
export async function GET() {
  const wwwUrl = await getWwwUrlServer(false) // Don't preserve path
  
  return Response.json({
    mainSiteUrl: wwwUrl,
    message: 'Redirect to main site available'
  })
}

// MIDDLEWARE USAGE
import { NextResponse } from 'next/server'

export function middleware(request: Request) {
  const url = new URL(request.url)
  
  if (hasSubdomain(url.host)) {
    const wwwUrl = toWwwUrl(request.url)
    return NextResponse.redirect(wwwUrl)
  }
  
  return NextResponse.next()
}
*/
