import axios from "axios";
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { setCookie, getCookie } from "cookies-next"; // Library for managing cookies in Next.js
import { jwtDecode } from "jwt-decode";
import moment from "moment";
import { API_URL } from "../../../../../config";

async function refreshAccessToken(token, req, res) {
  try {
    const refreshToken = await getCookie("refreshToken", { req, res });
    // console.log("\n\n\n\n\n\n\n\n\n\n\n\n", refreshToken);

    if (!refreshToken) {
      return res
        .status(401)
        .json({ message: "Refresh token is missing or invalid." });
    }

    const config = {
      url: `${API_URL}/auth/token/refresh/`,
      method: "post",
      headers: {
        "Content-Type": "application/json",
      },
      data: { refresh: refreshToken },
    };

    const response = await axios(config);
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

    // console.log(data);
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

const authOptions = (req, res) => ({
  // Configure one or more authentication providers
  providers: [
    // ...add more providers here
    CredentialsProvider({
      // The name to display on the sign in form (e.g. "Sign in with...")
      name: "Credentials",
      // `credentials` is used to generate a form on the sign in page.
      // You can specify which fields should be submitted, by adding keys to the `credentials` object.
      // e.g. domain, username, password, 2FA token, etc.
      // You can pass any HTML attribute to the <input> tag through the object.
      credentials: {
        email: {
          label: "Email",
          type: "email",
          placeholder: "jsmith",
        },
        password: {
          label: "Password",
          type: "password",
        },
      },
      async authorize(credentials) {
        const { email, password } = credentials;

        try {
          const config = {
            url: `${API_URL}/auth/login/`,
            method: "post",
            headers: {
              "Content-Type": "application/json",
            },
            data: { email, password },
          };
          const response = await axios(config);
          const { access, refresh } = response.data;
          const { exp } = jwtDecode(access);

          // Save the refresh token in an HTTP-only cookie
          setCookie("refreshToken", refresh, {
            req,
            res, // Required in Next.js API routes or SSR
            httpOnly: true,
            secure: process.env.NODE_ENV === "production", // Secure in production
            sameSite: "strict",
            path: "/",
          });

          console.log(
            "exp=========================",
            exp,
            moment(exp).minutes()
          );

          return {
            accessToken: access,
            // accessTokenExpires: Date.now() + (1 / 5) * 60 * 1000, // 5 minutes
          };
        } catch (error) {
          console.error("Login failed:", error);
          return null;
        }
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user, account, profile, isNewUser, trigger, session }) {
      if (user) {
        return {
          accessToken: user.accessToken,
          accessTokenExpires: user.accessTokenExpires,
          role: "admin",
        };
      }

      const { exp } = jwtDecode(token.accessToken);

      if (moment().unix() < exp) {
        return token;
      }

      console.log("refreshAccessToken will run");

      // Refresh the access token
      const refreshedToken = await refreshAccessToken(token, req, res);
      return refreshedToken;
    },

    async session({ session, token, user }) {
      if (!token?.accessToken) session.user = null;
      else session.user = token;

      return session;
    },

    // async signIn({ user, account, profile, email, credentials }) {
    //   return true
    // },
    // async redirect({ url, baseUrl }) {
    //   // Allows relative callback URLs
    //   if (url.startsWith("/")) return `${baseUrl}${url}`;
    //   // Allows callback URLs on the same origin
    //   else if (new URL(url).origin === baseUrl) return url;
    //   return baseUrl;
    // },
  },

  pages: {
    signIn: "/auth/login",
    signOut: "/auth/login",
  },
});

const handler = (req, res) => {
  return NextAuth(req, res, authOptions(req, res));
};

export {
  // The GET and POST methods are handled here
  handler as GET,
  handler as POST,
};
