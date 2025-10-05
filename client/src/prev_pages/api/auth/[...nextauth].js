// import type { NextApiRequest, NextApiResponse } from "next";
import NextAuth, { NextAuthOptions, User } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { setCookie, getCookie } from "cookies-next";
import { jwtDecode } from "jwt-decode";
import moment from "moment";
import { apiPost } from "@/actions/fetchApi";

async function refreshAccessToken(token, req, res) {
  try {
    const refreshToken = await getCookie("refreshToken", { req, res });

    if (!refreshToken) {
      return res
        .status(401)
        .json({ message: "Refresh token is missing or invalid." });
    }

    const response = await apiPost(`/auth/token/refresh/`, {
      refresh: refreshToken,
    });

    const data = response.data;

    const { exp } = jwtDecode(data.access);

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

    return {
      ...token,
      accessToken: data.access,
      exp,
    };
  } catch (error) {
    console.error("Failed to refresh access token:", error);
    return {
      // ...token,
      // error: "RefreshAccessTokenError",
    };
  }
}

export default async function auth(req, res) {
  return await NextAuth(req, res, {
    providers: [
      CredentialsProvider({
        name: "Credentials",
        credentials: {
          email: {
            label: "Email",
            type: "email",
            placeholder: "jsmith@example.com",
          },
          password: {
            label: "Password",
            type: "password",
            placeholder: "******",
          },
          subdomain: {
            label: "Subdomain",
            type: "text",
            placeholder: "school",
          },
        },

        async authorize(credentials) {
          const { email, password, subdomain } = credentials;

          try {
            const response = await apiPost(
              `/auth/login/`,
              {
                email,
                password,
              },
              { subdomain }
            );
            console.log("\n\n\n\n Response: ", response, "\n\n\n\n");
            const { access, refresh } = response.data;
            console.log("\n\n\n\n Access: ", access, "\n\n\n\n");

            const {
              exp,
              username,
              email: userEmail,
              first_name,
              last_name,
              image,
              gender,
              phone,
              role,
              school_logo,
              school_name,
              school_short_name,
            } = jwtDecode(access);

            setCookie("refreshToken", refresh, {
              req,
              res,
              httpOnly: true,
              secure: process.env.NODE_ENV === "production",
              sameSite: "strict",
              path: "/",
            });

            return {
              accessToken: access,
              accessTokenExpires: exp, // Here, save the expiration time for the access token.

              username,
              email: userEmail,
              fullName: `${first_name} ${last_name}`,
              firstName: first_name,
              lastName: last_name,
              schoolLogo: school_logo,
              schoolName: school_name,
              schoolShortName: school_short_name,
              image,
              gender,
              phone,
              role: role === "owner" ? "admin" : role,
              isOwner: role === "owner",
            };
          } catch (error) {
            // console.error("Login failed:", error.response);
            // console.error("Login failed:", error.request);
            throw error;
          }
        },
      }),
    ],

    callbacks: {
      async jwt({ token, user, account, profile, trigger, session }) {
        console.log(user, token);

        if (user) {
          return user;
        }

        // console.log(jwtDecode(token.accessToken));

        const { exp } = jwtDecode(token?.accessToken);

        if (moment().unix() < exp) {
          return token; // The token is still valid.
        }

        console.log("refreshAccessToken will run");

        // Refresh the access token
        const refreshedToken = await refreshAccessToken(token, req, res);
        return refreshedToken;
      },

      async session({ session, token }) {
        if (!token?.accessToken) session.user = null;
        else session.user = token;
        console.log(session);

        return session;
      },
    },

    pages: {
      signIn: "/login",
      signOut: "/login",
    },
  });
}
