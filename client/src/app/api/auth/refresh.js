import { setCookie, getCookie } from "cookies-next"; // Library for managing cookies in Next.js
import { jwtDecode } from "jwt-decode";
import axios from "axios";
import { API_URL } from "../../../../config";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ message: "Method not allowed" });
  }

  try {
    const refreshToken = await getCookie("refreshToken", { req, res }); // Get refresh token from HTTP-only cookie

    if (!refreshToken) {
      return res.status(401).json({ message: "Refresh token not found" });
    }

    const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
      refresh: refreshToken,
    });

    const data = response.data;

    if (data?.refresh) {
      setCookie("refreshToken", data.refresh, {
        req,
        res, // Required in Next.js API routes or SSR
        httpOnly: true,
        secure: process.env.NODE_ENV === "production", // Secure in production
        sameSite: "strict",
        path: "/",
      });
    }

    const { exp } = jwtDecode(data.access);

    return res.status(200).json({
      accessToken: data.access,
      accessTokenExpires: exp,
      role: "admin",
    });
  } catch (error) {
    console.error("Error refreshing token:", error);

    if (error.response) {
      // Django API returned a response (4xx or 5xx)
      const { status, data } = error.response;

      if (status == 400) {
        return res.status(400).json({ message: data.detail || "Bad request." });
      }

      if (status == 401) {
        return res.status(401).json({ message: data.detail || "Unauthorised" });
      }

      if (status >= 400 && status < 500) {
        return res
          .status(401)
          .json({ message: data.detail || "Invalid refresh token." });
      }

      if (status >= 500) {
        return res
          .status(500)
          .json({ message: "Server error while refreshing token." });
      }
    } else if (error.request) {
      // No response received from the Django API
      return res
        .status(503)
        .json({ message: "Unable to connect to the authentication server." });
    }

    // Catch any other unknown errors
    return res.status(500).json({ message: "An unexpected error occurred." });
  }
}
