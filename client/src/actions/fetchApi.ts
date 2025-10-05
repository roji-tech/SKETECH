"use server";

import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from "axios";
import { cookies as nextCookies } from "next/headers"; // avoid name clash with option `headers`
import { getSubdomainServer } from "./getHostInfo";

const DJANGO_API = process.env.DJANGO_API || "http://localhost:8000/api/v1";

// ===================== Types =====================
export interface QueryParams {
  [key: string]: string | number | boolean | null | undefined;
}

export interface ApiRequestOptions {
  endpoint: string;
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  data?: any;
  queryParams?: QueryParams;
  headers?: Record<string, string>;
  timeout?: number;
  withCredentials?: boolean;
  subdomain?: string;
  request?: Request | any;
  no_auth?: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?:
    | T
    | {
        errors?: Record<string, string[]>;
        message?: string;
        success?: boolean;
      };
  status?: number;
  statusText?: string;
  headers?: Record<string, string>;
  error?: any; // keep loose, but ensure it's plain
  message?: string;
}

interface AuthHeaders {
  Authorization?: string;
  "X-School"?: string;
}

// ===================== Utils =====================
/** Ensures headers are plain JSON-serializable. */
function normalizeHeaders(input: unknown): Record<string, string> {
  if (!input || typeof input !== "object") return {};
  // Axios v1 exposes AxiosHeaders with toJSON
  // We intentionally do a duck-typed check to avoid importing AxiosHeaders type
  // why: Next.js cannot serialize class instances (e.g., AxiosHeaders)
  const maybeAxiosHeaders = input as { toJSON?: () => any };
  const raw =
    typeof maybeAxiosHeaders.toJSON === "function"
      ? maybeAxiosHeaders.toJSON()
      : input;
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
    // coerce arrays/values to string for consistency
    if (Array.isArray(v)) out[String(k)] = v.map(String).join(", ");
    else if (v == null) out[String(k)] = "";
    else out[String(k)] = String(v);
  }
  return out;
}

/** Builds a query string from a flat params object. */
function buildQueryString(params?: QueryParams): string {
  if (!params || Object.keys(params).length === 0) return "";
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined) qs.append(key, String(value));
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

/** Derives auth-related headers from cookies and subdomain. */
async function getAuthHeaders(request?: Request | any): Promise<AuthHeaders> {
  const cookieStore = (request && request.cookies) || (await nextCookies());
  const accessToken =
    cookieStore?.get("access_token")?.value ||
    cookieStore?.get("accessToken")?.value ||
    cookieStore?.get("token")?.value;

  let subdomain = await getSubdomainServer();

  // If NO_SUBDOMAIN is set, try to get subdomain from client-side storage
  if (process.env.NO_SUBDOMAIN && typeof window !== "undefined" && !subdomain) {
    subdomain = sessionStorage.getItem("school_subdomain") || null;
  }

  const authHeaders: AuthHeaders = {};
  if (accessToken) authHeaders.Authorization = `Bearer ${accessToken}`;
  if (subdomain) authHeaders["X-School"] = subdomain;
  return authHeaders;
}

/** Determines if the payload is a FormData instance. */
function isFormData(data: unknown): boolean {
  // In Node 18+/Web, global FormData exists. We guard for SSR.
  return typeof FormData !== "undefined" && data instanceof FormData;
}

// ===================== Core Request =====================
export async function apiRequest<T = any>({
  endpoint,
  method = "GET",
  data = null,
  queryParams = {},
  headers = {},
  timeout = 30000,
  withCredentials = true,
  subdomain = "",
  request = null,
  no_auth = false,
}: ApiRequestOptions): Promise<ApiResponse<T>> {
  try {
    // Remove leading slash from endpoint if present
    const cleanEndpoint = endpoint.startsWith("/")
      ? endpoint.slice(1)
      : endpoint;

    // Build full URL with query parameters
    const queryString = buildQueryString(queryParams);
    const url = `${DJANGO_API}/${cleanEndpoint}${queryString}`;

    let authHeaders: AuthHeaders = {};
    if (!no_auth) {
      try {
        authHeaders = await getAuthHeaders(request);
      } catch (error) {
        console.error("Failed to get auth headers:", error);
      }
    }
    // Get authentication headers

    if (!authHeaders["X-School"] && subdomain) {
      authHeaders["X-School"] = subdomain;
    }

    console.log("\n\n\n\n Auth Headers: ", no_auth, authHeaders, "\n\n\n\n");

    const useFormData = isFormData(data);
    const mergedHeaders: Record<string, string> = {
      // Only set JSON content-type when not sending FormData and caller didn't set it.
      ...(useFormData ? {} : { "Content-Type": "application/json" }),
      ...authHeaders,
      ...headers,
    };

    const config: AxiosRequestConfig = {
      method: method.toUpperCase() as AxiosRequestConfig["method"],
      url,
      headers: mergedHeaders,
      timeout,
      withCredentials,
      ...(data != null &&
      ["POST", "PUT", "PATCH"].includes(method.toUpperCase())
        ? { data }
        : {}),
      // why: ensure Node follows redirects/cookies as needed; keep defaults otherwise
    };

    const response: AxiosResponse<T> = await axios<T>(config);

    console.log(
      `Response from Django API: ${method} ${url}`,
      response.data,
      response.status,
      response.headers
    );

    return {
      success: true,
      data: response.data,
      status: response.status,
      headers: normalizeHeaders(response.headers), // <- plain object
    };
  } catch (err) {
    const axiosError = err as AxiosError;

    if (axiosError?.response) {
      // Server responded with an error status
      console.log(
        "\n\n\n\n Axios Error Response: ",
        axiosError.response.status,
        axiosError.response.statusText,
        axiosError.response.data
      );

      const data =
        typeof axiosError.response.data == "object"
          ? (axiosError.response.data as any)
          : { errors: "____" };

      for (const [key, value] of Object.entries(
        Object.keys(data || { errors: "___" })
      )) {
        console.log(key, value, data?.[value]);
      }

      console.log("\n\n\n\n");

      return {
        success: false,
        data: axiosError?.response?.data || {},
        error: ensurePlain(axiosError.response.data),
        status: axiosError.response.status,
        statusText: axiosError.response.statusText,
        headers: normalizeHeaders(axiosError.response.headers),
        message:
          (safeGet(axiosError.response.data, ["message"]) as
            | string
            | undefined) || axiosError.message,
      };
    }

    if (axiosError?.request) {
      // Request made but no response received
      return {
        success: false,
        error: "Network Error",
        message: "No response received from server",
      };
    }

    // Something else happened during setup
    return {
      success: false,
      error: ensurePlain(axiosError.message || err),
      message: axiosError.message || String(err),
    };
  }
}

// ===================== Verb Helpers =====================
export async function setSubdomain(subdomain: string) {
  const cookieStore = await nextCookies();

  cookieStore.set("school_subdomain", subdomain, {
    httpOnly: false,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
  });
}

// ===================== Verb Helpers =====================
export async function apiGet<T = any>(
  endpoint: string,
  options: Partial<ApiRequestOptions> = {}
): Promise<ApiResponse<T>> {
  return apiRequest<T>({ endpoint, method: "GET", ...options });
}

export async function apiPost<T = any>(
  endpoint: string,
  data: any,
  options: Partial<ApiRequestOptions> = {}
): Promise<ApiResponse<T>> {
  return apiRequest<T>({ endpoint, method: "POST", data, ...options });
}

export async function apiPut<T = any>(
  endpoint: string,
  data: any,
  options: Partial<ApiRequestOptions> = {}
): Promise<ApiResponse<T>> {
  return apiRequest<T>({ endpoint, method: "PUT", data, ...options });
}

export async function apiPatch<T = any>(
  endpoint: string,
  data: any,
  options: Partial<ApiRequestOptions> = {}
): Promise<ApiResponse<T>> {
  return apiRequest<T>({ endpoint, method: "PATCH", data, ...options });
}

export async function apiDelete<T = any>(
  endpoint: string,
  options: Partial<ApiRequestOptions> = {}
): Promise<ApiResponse<T>> {
  return apiRequest<T>({ endpoint, method: "DELETE", ...options });
}

/** Specialized helper for file uploads (FormData). */
export async function apiUpload<T = any>(
  endpoint: string,
  formData: FormData,
  options: Partial<ApiRequestOptions> = {}
): Promise<ApiResponse<T>> {
  // Pass FormData as `data`; apiRequest will omit JSON content-type automatically
  return apiRequest<T>({
    endpoint,
    method: "POST",
    data: formData,
    headers: { ...(options.headers || {}) },
    ...options,
  });
}

// ===================== Safety Helpers =====================
/** Ensure values are plain JSON-serializable (no class instances). */
function ensurePlain<T>(value: T): T {
  try {
    // Fast path: stringify/parse to normalize special objects; small and safe for typical payload sizes
    return JSON.parse(JSON.stringify(value)) as T;
  } catch {
    return (value != null ? String(value) : "") as unknown as T;
  }
}

/** Safe getter for nested fields on unknown structures. */
function safeGet(obj: unknown, path: (string | number)[]): unknown {
  let cur: any = obj;
  for (const key of path) {
    if (cur && typeof cur === "object" && key in cur) cur = cur[key];
    else return undefined;
  }
  return cur;
}
