import NextAuth, {
  DefaultSession,
  NextAuthOptions,
  User,
  Session,
} from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { setCookie, getCookie } from "cookies-next";
import { cookies } from "next/headers";
import { JwtPayload, jwtDecode } from "jwt-decode";
import moment from "moment";
import { apiPost } from "@/actions/fetchApi";
import { UserType } from "@/types/intefaces";

// Extend the built-in session types
declare module "next-auth" {
  interface Session {
    user: UserType;
  }

  interface JWT {
    accessToken?: string;
    accessTokenExpires?: number;
    refreshToken?: string;
    username?: string;
    fullName?: string;
    firstName?: string;
    lastName?: string;
    schoolLogo?: string;
    schoolName?: string;
    schoolShortName?: string;
    gender?: string;
    phone?: string;
    role?: string;
    isOwner?: boolean;
    error?: string;
  }
}

interface TokenResponse {
  access: string;
  refresh: string;
}

interface UserAuth extends User {
  accessToken: string;
  accessTokenExpires: number;
  username: string;
  email: string;

  fullName: string;
  firstName: string;
  lastName: string;
  schoolLogo?: string;
  schoolName?: string;
  schoolShortName?: string;
  image?: string;
  gender?: string;
  phone?: string;
  role?: string;
  isOwner?: boolean;
}

interface UserJwtPayload extends JwtPayload {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  image?: string;
  gender?: string;
  phone?: string;
  role: string;
  school_logo?: string;
  school_name?: string;
  school_short_name?: string;
  exp: number;
}

const authOptions: NextAuthOptions = {
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
        subdomain: { label: "Subdomain", type: "text", placeholder: "school" },
      },
      async authorize(credentials): Promise<UserAuth | null> {
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Email and password are required");
        }

        console.log(
          "\n\n\n\n Credentials in app/api/auth/[...nextauth]/route.ts: ",
          credentials,
          "\n\n\n\n"
        );

        const { email, password, subdomain } = credentials;

        try {
          const response = await apiPost<TokenResponse>(
            `/auth/login/`,
            { email, password },
            { subdomain }
          );

          if (!response.success) {
            console.log("\n\n\n\n Response: ", response, "\n\n\n\n");
            throw response;
          }

          if (
            typeof response?.data !== "object" ||
            "access"! in response?.data
          ) {
            console.error("Invalid response from auth server:", response);
            throw new Error(
              "Authentication failed: Invalid response from server"
            );
          }

          if (typeof response?.data == "object" && "access" in response?.data) {
            const data = response.data as TokenResponse;
            const { access } = data;
            let refresh = "";
            if (typeof data == "object" && "refresh" in data) {
              const { refresh } = data;
            }

            try {
              const decoded = jwtDecode<UserJwtPayload>(access);

              if (!decoded || !decoded.exp) {
                throw new Error("Invalid token format");
              }

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
              } = decoded;

              if (
                !username ||
                !userEmail ||
                !first_name ||
                !last_name ||
                !role
              ) {
                throw new Error(
                  "Authentication failed: Incomplete user information"
                );
              }

              // Set refresh token in HTTP-only cookie
              setCookie("accessToken", access, {
                httpOnly: true,
                secure: process.env.NODE_ENV === "production",
                sameSite: "strict",
                path: "/",
              });

              // Set refresh token in HTTP-only cookie
              setCookie("refreshToken", refresh, {
                httpOnly: true,
                secure: process.env.NODE_ENV === "production",
                sameSite: "strict",
                path: "/",
              });

              const cookieStore = await cookies();

              cookieStore.set("accessToken", access, {
                httpOnly: true,
                secure: process.env.NODE_ENV === "production",
                sameSite: "strict",
                path: "/",
              });

              cookieStore.set("refreshToken", refresh, {
                httpOnly: true,
                secure: process.env.NODE_ENV === "production",
                sameSite: "strict",
                path: "/",
              });

              return {
                id: username,
                name: `${first_name} ${last_name}`.trim(),
                email: userEmail,
                accessToken: access,
                accessTokenExpires: exp * 1000, // Convert to milliseconds
                username,
                fullName: `${first_name} ${last_name}`.trim(),
                firstName: first_name,
                lastName: last_name,
                schoolLogo: school_logo,
                schoolName: school_name,
                schoolShortName: school_short_name,
                image,
                gender,
                phone,
                role,
                isOwner: role === "owner",
              };
            } catch (tokenError) {
              console.error("Error decoding JWT token:", tokenError);
              throw new Error("Authentication failed: Invalid token");
            }
          }

          return null;
        } catch (error: any) {
          console.error("Authentication error:", error);

          // Handle different types of errors
          if (error.response) {
            // API returned an error response
            const { status, data } = error.response;
            if (status === 401) {
              throw new Error("Invalid email or password");
            } else if (status >= 400 && status < 500) {
              throw new Error(
                data?.message || "Authentication failed: Invalid request"
              );
            } else {
              throw new Error("Authentication server error");
            }
          } else if (error.request) {
            // Request was made but no response received
            throw new Error("Unable to connect to the authentication server");
          } else {
            throw new Error(error.message || "Authentication failed");
          }
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user, trigger, session }) {
      if (trigger === "update" && session) {
        return { ...token, ...session.user };
      }

      if (user) {
        return { ...token, ...user };
      }

      const refreshToken = getCookie("refreshToken");
      const tokenExp = token.accessTokenExpires as number;

      // Return previous token if it's still valid
      if (tokenExp && moment().valueOf() < tokenExp) {
        return token;
      }

      // Try to refresh the token if it's expired
      if (refreshToken) {
        try {
          const response = await apiPost<TokenResponse>(
            `/auth/token/refresh/`,
            {
              refresh: refreshToken,
            }
          );

          const { access, refresh } = response.data as any;
          const { exp } = jwtDecode<UserJwtPayload>(access);

          if (refresh) {
            await setCookie("refreshToken", refresh, {
              httpOnly: true,
              secure: process.env.NODE_ENV === "production",
              sameSite: "strict",
              path: "/",
            });
          }

          return {
            ...token,
            accessToken: access,
            accessTokenExpires: exp * 1000, // Convert to milliseconds
          };
        } catch (error) {
          console.error("Failed to refresh token:", error);
          return { ...token, error: "RefreshAccessTokenError" };
        }
      }

      return token;
    },
    async session({ session, token }): Promise<Session> {
      if (token?.error) {
        return { ...session, error: token.error } as any;
      }

      if (token?.accessToken) {
        const newUser = {
          ...session?.user,
          accessToken: token.accessToken,
          accessTokenExpires: token.accessTokenExpires,
          username: token?.username,
          email: token?.email,
          name: token?.name || token?.fullName || null,
          fullName: token?.fullName,
          firstName: token?.firstName,
          lastName: token?.lastName,
          schoolLogo: token?.schoolLogo,
          schoolName: token?.schoolName,
          schoolShortName: token?.schoolShortName,
          image: token?.image || null,
          gender: token?.gender,
          phone: token?.phone,
          role: token?.role,
          isOwner: token?.isOwner,
        };

        session.user = newUser as any;
      }

      return session;
    },
  },
  events: {
    async signOut() {
      const cookieStore = await cookies();
      cookieStore.delete("accessToken");
      cookieStore.delete("refreshToken");
      cookieStore.delete("next-auth.session-token");
      console.log("\n\n\n\n\nDeleted cookies\n\n\n\n\n");
    },
  },
  pages: {
    signIn: "/login",
    signOut: "/login",
  },
  session: {
    strategy: "jwt",
  },
  secret: process.env.NEXTAUTH_SECRET,
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
