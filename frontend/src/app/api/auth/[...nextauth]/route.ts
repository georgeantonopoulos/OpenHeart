/**
 * NextAuth.js API Route for OpenHeart Cyprus.
 *
 * Only exports HTTP method handlers (GET, POST) as required by Next.js App Router.
 * Auth configuration is in @/lib/auth-options.ts.
 */

import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth-options";

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
