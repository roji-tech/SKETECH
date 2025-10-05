"use server";

import { cookies } from "next/headers";

export const customSignOut = async () => {
  // Remove the refresh token
  const cookieStore = await cookies();
  cookieStore.delete("refreshToken");
  cookieStore.delete("next-auth.session-token");
  cookieStore.delete("next-auth.csrf-token");
  cookieStore.delete("next-auth.callback-url");
  cookieStore.delete("school_subdomain");

  // If NO_SUBDOMAIN is set, clear the subdomain from cookies and sessionStorage
  if (process.env.NO_SUBDOMAIN) {
    // Delete the subdomain cookie by setting it to expire in the past

    // Clear from sessionStorage if running in browser
    if (typeof window !== "undefined" && window.document !== null) {
      document.cookie =
        "school_subdomain=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      sessionStorage.removeItem("school_subdomain");
    }
  }

  return { success: true, message: "Refresh token removed" };
};
