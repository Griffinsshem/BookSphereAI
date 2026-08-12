import { AppShell } from "@/components/shared/AppShell";

/**
 * Applies ONLY to routes inside the (dashboard) route group --
 * Resources, Services, Bookings, Team, and the dashboard home page.
 * (auth) routes (login/register/invite-accept) are siblings of this
 * group, not children of it, so they deliberately never get this
 * shell -- they stay centered and minimal, which is correct for
 * pages a logged-out visitor might land on.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
