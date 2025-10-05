"use server";

import { cookies } from "next/headers";

export const customSignOut = async () => {
  // Remove the refresh token
  const cookieStore = await cookies();
  cookieStore.delete("refreshToken");
  cookieStore.delete("next-auth.session-token");
  cookieStore.delete("next-auth.csrf-token");
  cookieStore.delete("next-auth.callback-url");

  return { success: true, message: "Refresh token removed" };
};
