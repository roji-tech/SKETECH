import { signOut, getSession, signIn } from "next-auth/react";
import axiosInstance from "./axiosInstance";

export const handleSignOut = async () => {
  Promise.all([
    await signOut({ callbackUrl: "/login" }),
    await fetch("/api/auth/signout", { method: "POST" }),
  ])
    .then((res) => console.log("successfully signed out"))
    .catch((err) => console.log("error while signing out", err));
};

export async function fetchApi(config) {
  try {
    const response = await axiosInstance(config);
    return response;
  } catch (error) {
    console.error("Failed to fetch data:", error);
    throw error;
  }
}

export async function updateSessionWithToken(accessToken) {
  const session = await getSession();
  if (session) {
    session.user.accessToken = accessToken;
  } else {
    await signIn(); // Reinitialize the session if necessary
  }
}
