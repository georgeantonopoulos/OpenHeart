import { redirect } from "next/navigation";

/**
 * Procedures index page - redirects to worklist.
 */
export default function ProceduresPage() {
  redirect("/procedures/worklist");
}
