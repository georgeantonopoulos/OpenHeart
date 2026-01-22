/**
 * NextAuth.js type extensions for OpenHeart Cyprus.
 *
 * Extends default Session and User types to include:
 * - User role (admin, cardiologist, nurse, etc.)
 * - Clinic assignment (ID and name)
 * - Backend access token for API calls
 */

import { DefaultSession, DefaultUser } from "next-auth";
import { DefaultJWT } from "next-auth/jwt";

declare module "next-auth" {
  /**
   * Extended Session interface with OpenHeart-specific fields.
   */
  interface Session extends DefaultSession {
    user: {
      /** User's database ID */
      id: string;
      /** User's role at their primary clinic */
      role: string;
      /** Primary clinic ID for multi-tenant context */
      clinicId: number;
      /** Primary clinic name for display */
      clinicName: string;
    } & DefaultSession["user"];

    /** Backend JWT access token for API calls */
    accessToken: string;

    /** Error state (e.g., "RefreshAccessTokenError") */
    error?: string;
  }

  /**
   * Extended User interface returned from authorize().
   */
  interface User extends DefaultUser {
    /** User's role at their primary clinic */
    role: string;
    /** Primary clinic ID */
    clinicId: number;
    /** Primary clinic name */
    clinicName: string;
    /** Backend JWT access token */
    accessToken: string;
    /** Backend JWT refresh token */
    refreshToken: string;
    /** Access token expiry timestamp (Unix seconds) */
    expiresAt: number;
  }
}

declare module "next-auth/jwt" {
  /**
   * Extended JWT interface for token storage.
   */
  interface JWT extends DefaultJWT {
    /** User's database ID */
    id?: string;
    /** User's role */
    role?: string;
    /** Clinic ID */
    clinicId?: number;
    /** Clinic name */
    clinicName?: string;
    /** Backend access token */
    accessToken?: string;
    /** Backend refresh token */
    refreshToken?: string;
    /** Access token expiry timestamp */
    expiresAt?: number;
    /** Error state */
    error?: string;
  }
}
