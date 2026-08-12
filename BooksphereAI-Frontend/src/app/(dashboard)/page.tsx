"use client";

import Link from "next/link";
import { CalendarDays, Tags, Users, Warehouse } from "lucide-react";
import { useOrgStore } from "@/lib/org-store";
import { useAuthStore } from "@/lib/auth-store";
import { useBookingsList } from "@/features/bookings/hooks/useBookings";

const QUICK_LINKS = [
  { href: "/resources", label: "Resources", icon: Warehouse, description: "Rooms, equipment, and staff" },
  { href: "/services", label: "Services", icon: Tags, description: "What customers book" },
  { href: "/bookings", label: "Bookings", icon: CalendarDays, description: "Create and manage bookings" },
  { href: "/team", label: "Team", icon: Users, description: "Invite and manage members" },
];

function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function HomePage() {
  const currentOrg = useOrgStore((s) => s.currentOrg);
  const user = useAuthStore((s) => s.user);
  const { data: bookingsData } = useBookingsList(currentOrg?.id);

  const upcomingConfirmed = (bookingsData?.items ?? [])
    .filter((b) => b.status === "confirmed" && new Date(b.start_time) > new Date())
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    .slice(0, 5);

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-semibold">
        {user ? `Welcome back, ${user.full_name.split(" ")[0]}` : "Welcome"}
      </h1>
      <p className="mb-8 text-sm text-gray-600">
        {currentOrg ? `${currentOrg.name} · ${currentOrg.role}` : "Loading your organization…"}
      </p>

      <div className="mb-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {QUICK_LINKS.map((link) => {
          const Icon = link.icon;
          return (
            <Link
              key={link.href}
              href={link.href}
              className="flex flex-col items-start gap-2 rounded-lg border border-border bg-card p-4 shadow-sm transition-all hover:border-primary hover:shadow-md"
            >
              <Icon className="h-5 w-5 text-gray-700" />
              <span className="text-sm font-medium">{link.label}</span>
              <span className="text-xs text-gray-500">{link.description}</span>
            </Link>
          );
        })}
      </div>

      <h2 className="mb-4 text-lg font-medium">Upcoming bookings</h2>
      {upcomingConfirmed.length === 0 ? (
        <p className="text-sm text-gray-600">
          Nothing coming up.{" "}
          <Link href="/bookings" className="underline">
            Create a booking
          </Link>{" "}
          to get started.
        </p>
      ) : (
        <ul className="divide-y divide-border rounded-lg border border-border bg-card shadow-sm">
          {upcomingConfirmed.map((booking) => (
            <li key={booking.id} className="px-4 py-3">
              <p className="text-sm font-medium">{formatDateTime(booking.start_time)}</p>
              {booking.notes && <p className="text-xs text-gray-500">{booking.notes}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
