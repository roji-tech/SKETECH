// app/api/refresh/route.ts

import { NextResponse } from "next/server"; // Import Next.js response handling
import { setCookie, getCookie } from "cookies-next"; // Library for managing cookies in Next.js
import { jwtDecode } from "jwt-decode";
import axios from "axios";
import { API_URL } from "../../../../../config";

// Define the expected structure of the request body
interface RefreshTokenRequest {
  refreshToken: string;
}

// Define the structure of the response from the token refresh API
interface RefreshTokenResponse {
  access: string;
  refresh?: string;
}

// Define the structure of the decoded JWT
interface DecodedToken {
  exp: number; // Expiration time as a Unix timestamp
}

// Handle POST requests
export async function POST(req: any) {
  // Parse the incoming request body
  const { refreshToken }: RefreshTokenRequest = await req.json();

  try {
    // Get the refresh token from HTTP-only cookie
    const token = getCookie("refreshToken", { req });

    if (!token) {
      return NextResponse.json(
        { message: "Refresh token not found" },
        { status: 401 }
      );
    }

    // Make the API call to refresh the token
    const response = await axios.post<RefreshTokenResponse>(
      `${API_URL}/auth/token/refresh/`,
      { refresh: token }
    );

    const data = response.data;

    // Set the new refresh token in the cookie
    if (data?.refresh) {
      setCookie("refreshToken", data.refresh, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production", // Secure in production
        sameSite: "strict",
        path: "/",
      });
    }

    // Decode the access token to get the expiration time
    const { exp } = jwtDecode<DecodedToken>(data.access);

    return NextResponse.json(
      {
        accessToken: data.access,
        accessTokenExpires: exp,
        role: "admin",
      },
      { status: 200 }
    );
  } catch (error: any) {
    console.error("Error refreshing token:", error);

    if (axios.isAxiosError(error) && error.response) {
      // Django API returned a response (4xx or 5xx)
      const { status, data } = error.response;

      if (status >= 400 && status < 500) {
        return NextResponse.json(
          { message: data.detail || "Invalid refresh token." },
          { status: status }
        );
      }

      return NextResponse.json(
        { message: data.detail || "Server error while refreshing token." },
        { status: 500 }
      );
    } else if (error.request) {
      // No response received from the Django API
      return NextResponse.json(
        { message: "Unable to connect to the authentication server." },
        { status: 503 }
      );
    }

    // Catch any other unknown errors
    return NextResponse.json(
      { message: "An unexpected error occurred." },
      { status: 500 }
    );
  }
}
