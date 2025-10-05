import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { extractSubdomain } from "@/utils/hostInfoUtils";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const setCookie = (name: string, value: string, days: number) => {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Strict; Secure`;
};

/**
 * Get the actual path with subdomain prefix
 * @param path The path to append after the subdomain
 * @returns The full path with subdomain (e.g., "/dashboard" -> "/subdomain/dashboard")
 */
export const getActualPath = (path: string): string => {
  if (typeof window === 'undefined') return path;
  
  const subdomain = extractSubdomain(window.location.host);
  // For the root path, we don't need to add a trailing slash
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  
  if (!subdomain || subdomain === 'www') {
    return cleanPath;
  }
  
  return `${cleanPath}`;
};

/**
 * Get the API URL with the correct subdomain prefix
 * @param path The API endpoint path
 * @returns The full API URL with subdomain (e.g., "/auth/login" -> "/subdomain/api/v1/auth/login")
 */
export const getApiUrl = (path: string): string => {
  if (typeof window === 'undefined') return `/api/v1${path}`;
  
  const subdomain = extractSubdomain(window.location.host);
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  
  if (!subdomain || subdomain === 'www') {
    return `/api/v1${cleanPath}`;
  }
  
  return `/api/v1${cleanPath}`;
};

/**
 * Get the current subdomain from the URL
 * @returns The current subdomain or null if not found
 */
export const getCurrentSubdomain = (): string | null => {
  if (typeof window === 'undefined') return null;
  return extractSubdomain(window.location.host);
};
