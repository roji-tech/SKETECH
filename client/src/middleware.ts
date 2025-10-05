import withAuth from "next-auth/middleware";
import { NextRequest, NextResponse } from "next/server";
import { isAdmin, isParent, isStaff, isStudent } from "./utils/permissions";

// Define role-based access paths
const rolePaths = {
  admin: "/admin",
  student: "/student",
  parent: "/parent",
  staff: "/staff", // Changed from "/teacher" to match the role
};

// List of public paths that don't require authentication
const publicPaths = [
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
  "/api/auth",
  "/_next",
  "/favicon.ico",
];

// Middleware to handle role-based access
export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token;
    const pathname = req.nextUrl.pathname;
    console.log(token, pathname);
    // Skip middleware for public paths
    if (publicPaths.some((path) => pathname.startsWith(path))) {
      return NextResponse.next();
    }

    // If no token, redirect to login
    if (!token) {
      const loginUrl = new URL("/login", req.nextUrl.origin);
      loginUrl.searchParams.set("callbackUrl", pathname);
      return NextResponse.redirect(loginUrl);
    }

    // Role-based access control
    const userRole = token.role?.toString().toLowerCase() || "";

    // Admin routes
    if (pathname.startsWith(rolePaths.admin) && !isAdmin(userRole)) {
      return NextResponse.redirect(
        new URL("/unauthorized?message=Admin access required", req.url)
      );
    }

    // Student routes
    if (pathname.startsWith(rolePaths.student) && !isStudent(userRole)) {
      return NextResponse.redirect(
        new URL("/unauthorized?message=Student access required", req.url)
      );
    }

    // Parent routes
    if (pathname.startsWith(rolePaths.parent) && !isParent(userRole)) {
      return NextResponse.redirect(
        new URL("/unauthorized?message=Parent access required", req.url)
      );
    }

    // Teacher/Staff routes
    if (pathname.startsWith(rolePaths.staff) && !isStaff(userRole)) {
      return NextResponse.redirect(
        new URL("/unauthorized?message=Teacher access required", req.url)
      );
    }

    // For all other protected routes, just verify they're authenticated
    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => {
        console.log("\n\n\n\ntoken", token);
        // User must have a valid token to proceed
        return !!token;
      },
    },
    pages: {
      signIn: "/login",
      error: "/unauthorized",
    },
  }
);

// Matcher configuration for the protected routes
export const config = {
  matcher: [
    "/dashboard/:path*",
    "/admin/:path*",
    "/student/:path*",
    "/parent/:path*",
    "/staff/:path*",
    "/list/:path*",
    "/profile",
    "/settings",
  ],
};
















// // middleware.ts
// const BASE_DOMAIN = (process.env.BASE_DOMAIN || "").trim().toLowerCase();

// /** Light re-implementation inline to avoid importing server-only headers into edge */
// function splitHostPort(host: string): [string, string?] {
//   const idx = host.lastIndexOf(":");
//   if (idx > -1 && !host.includes("]")) return [host.slice(0, idx), host.slice(idx + 1)];
//   return [host, undefined];
// }
// function isIPv6(h: string) { return h.startsWith("[") && h.endsWith("]"); }
// function isIPv4(h: string) { return /^\d{1,3}(\.\d{1,3}){3}$/.test(h); }
// function isIp(h: string) { return isIPv4(h) || isIPv6(h); }
// function isLocalhostLike(h: string) {
//   return h === "localhost" || h.endsWith(".localhost") || h === "[::1]" || h === "127.0.0.1" || h === "0.0.0.0";
// }

// function canonicalizeHostEdge(hostWithPort: string): { host: string; changed: boolean } {
//   if (!hostWithPort) return { host: hostWithPort, changed: false };

//   let host = hostWithPort;
//   let port: string | undefined;
//   if (!isIPv6(hostWithPort)) {
//     [host, port] = splitHostPort(hostWithPort);
//   }

//   const original = hostWithPort;
//   const hostname = host.toLowerCase();
//   const bd = BASE_DOMAIN;
//   const isVercelBase = bd.endsWith(".vercel.app");

//   // Local / IP
//   if (isLocalhostLike(hostname) || isIp(hostname)) {
//     const canonical = hostname === "localhost" || isIp(hostname) ? hostname : "localhost";
//     const result = port ? `${canonical}:${port}` : canonical;
//     return { host: result, changed: result !== original };
//   }

//   if (bd) {
//     if (hostname === bd) {
//       const result = port ? `${hostname}:${port}` : hostname;
//       return { host: result, changed: result !== original };
//     }
//     if (hostname.endsWith("." + bd)) {
//       if (isVercelBase) {
//         const result = port ? `${bd}:${port}` : bd; // strip ANY subdomain on vercel base
//         return { host: result, changed: result !== original };
//       } else {
//         const result = port ? `www.${bd}:${port}` : `www.${bd}`; // replace subdomain with 'www'
//         return { host: result, changed: result !== original };
//       }
//     }
//   }

//   return { host: original, changed: false };
// }

// export function middleware(req: NextRequest) {
//   const url = req.nextUrl.clone();

//   // Maintain protocol via proxy header when present
//   const xfProto = req.headers.get("x-forwarded-proto");
//   if (xfProto) url.protocol = `${xfProto}:`;

//   // Canonicalize the host
//   const { host: newHost, changed } = canonicalizeHostEdge(url.host);
//   if (changed) {
//     url.host = newHost; // keep pathname/search/hash as-is
//     return NextResponse.redirect(url, 308);
//   }

//   return NextResponse.next();
// }

// // Optionally limit which paths to run on:
// // export const config = { matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'] };
