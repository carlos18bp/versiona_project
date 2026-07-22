import { redirect } from 'next/navigation';

/** The board lives at /projects (docs/plan/04 §2); /dashboard survives only
 * as a redirect for the template auth flows that still land here. */
export default function DashboardRedirect() {
  redirect('/projects');
}
