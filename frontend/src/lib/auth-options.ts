/**
 * NextAuth.js configuration for OpenHeart Cyprus.
 *
 * Separated from the route handler to allow importing in server components
 * without triggering Next.js App Router route export restrictions.
 */

import { type NextAuthOptions, type User } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const API_URL = process.env.INTERNAL_API_URL || "http://backend:8000";

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    user_id: number;
    email: string;
    full_name: string;
    role: string;
    clinic_id: number;
    clinic_name: string;
  };
}

interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

async function refreshAccessToken(refreshToken: string): Promise<{
  accessToken: string;
  expiresAt: number;
} | null> {
  try {
    const response = await fetch(`${API_URL}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      return null;
    }

    const data: RefreshResponse = await response.json();

    return {
      accessToken: data.access_token,
      expiresAt: Math.floor(Date.now() / 1000) + data.expires_in,
    };
  } catch (error) {
    console.error("Token refresh failed:", error);
    return null;
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },

      async authorize(credentials): Promise<User | null> {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          const response = await fetch(`${API_URL}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!response.ok) {
            return null;
          }

          const data: LoginResponse = await response.json();

          return {
            id: String(data.user.user_id),
            email: data.user.email,
            name: data.user.full_name,
            role: data.user.role,
            clinicId: data.user.clinic_id,
            clinicName: data.user.clinic_name,
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            expiresAt: Math.floor(Date.now() / 1000) + data.expires_in,
          };
        } catch (error) {
          console.error("Authentication error:", error);
          return null;
        }
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = user.role;
        token.clinicId = user.clinicId;
        token.clinicName = user.clinicName;
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.expiresAt = user.expiresAt;
      }

      const now = Math.floor(Date.now() / 1000);
      const expiresAt = token.expiresAt as number;

      if (expiresAt && now >= expiresAt - 60) {
        const refreshToken = token.refreshToken as string;
        const refreshed = await refreshAccessToken(refreshToken);

        if (refreshed) {
          token.accessToken = refreshed.accessToken;
          token.expiresAt = refreshed.expiresAt;
        } else {
          token.error = "RefreshAccessTokenError";
        }
      }

      return token;
    },

    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
        session.user.clinicId = token.clinicId as number;
        session.user.clinicName = token.clinicName as string;
      }

      session.accessToken = token.accessToken as string;

      if (token.error) {
        session.error = token.error as string;
      }

      return session;
    },
  },

  pages: {
    signIn: "/login",
    error: "/login",
  },

  session: {
    strategy: "jwt",
    maxAge: 7 * 24 * 60 * 60,
  },

  debug: process.env.NODE_ENV === "development",
};
