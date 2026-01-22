/**
 * NextAuth.js API Route for OpenHeart Cyprus.
 *
 * Configures authentication with credentials provider calling the FastAPI backend.
 * Handles JWT token management and session synchronization.
 */

import NextAuth, { type NextAuthOptions, type User } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

// Server-side API URL (for NextAuth authorize which runs in the container)
// Falls back to Docker service name if INTERNAL_API_URL not set
const API_URL = process.env.INTERNAL_API_URL || "http://backend:8000";

/**
 * Response from backend /api/auth/login endpoint.
 */
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

/**
 * Response from backend /api/auth/refresh endpoint.
 */
interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * Refresh the access token using the refresh token.
 */
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
            // Return null for any error - NextAuth will show generic error
            return null;
          }

          const data: LoginResponse = await response.json();

          // Return user object with all required fields for NextAuth
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
    /**
     * JWT callback - called when JWT is created or updated.
     *
     * On initial sign in, copy user data to token.
     * On subsequent calls, check if access token needs refresh.
     */
    async jwt({ token, user }) {
      // Initial sign in - copy user data to token
      if (user) {
        token.id = user.id;
        token.role = user.role;
        token.clinicId = user.clinicId;
        token.clinicName = user.clinicName;
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.expiresAt = user.expiresAt;
      }

      // Check if access token is expired or about to expire (within 60 seconds)
      const now = Math.floor(Date.now() / 1000);
      const expiresAt = token.expiresAt as number;

      if (expiresAt && now >= expiresAt - 60) {
        // Token expired or expiring soon - attempt refresh
        const refreshToken = token.refreshToken as string;
        const refreshed = await refreshAccessToken(refreshToken);

        if (refreshed) {
          token.accessToken = refreshed.accessToken;
          token.expiresAt = refreshed.expiresAt;
        } else {
          // Refresh failed - mark token as expired
          // This will force re-login on next session check
          token.error = "RefreshAccessTokenError";
        }
      }

      return token;
    },

    /**
     * Session callback - called when session is accessed.
     *
     * Expose role, clinic info, and access token to client.
     */
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
        session.user.clinicId = token.clinicId as number;
        session.user.clinicName = token.clinicName as string;
      }

      // Expose access token for API calls
      session.accessToken = token.accessToken as string;

      // Expose error if token refresh failed
      if (token.error) {
        session.error = token.error as string;
      }

      return session;
    },
  },

  pages: {
    signIn: "/login",
    error: "/login", // Redirect to login on error
  },

  session: {
    strategy: "jwt",
    // Match refresh token expiry (7 days)
    maxAge: 7 * 24 * 60 * 60,
  },

  // Enable debug in development
  debug: process.env.NODE_ENV === "development",
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
