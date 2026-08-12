"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  CalendarDays,
  LayoutDashboard,
  LogOut,
  Menu,
  Tags,
  Users,
  Warehouse,
  X,
} from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { useLogout } from "@/features/auth/hooks/useAuth";
import { OrgSwitcher } from "./OrgSwitcher";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/resources", label: "Resources", icon: Warehouse },
  { href: "/services", label: "Services", icon: Tags },
  { href: "/bookings", label: "Bookings", icon: CalendarDays },
  { href: "/team", label: "Team", icon: Users },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const handleLogout = async () => {
    await logout.mutateAsync();
    router.push("/login");
  };

  const NavLinks = (
    <nav className="flex flex-1 flex-col gap-1 px-3">
      {NAV_ITEMS.map((item) => {
        const isActive =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setMobileNavOpen(false)}
            className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              isActive
                ? "bg-gray-900 text-white"
                : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 flex-col border-r border-gray-200 py-6 md:flex">
        <div className="mb-6 px-4 text-lg font-semibold">BookSphere AI</div>
        {NavLinks}
        <div className="mt-auto px-3 pt-4">
          <button
            onClick={handleLogout}
            disabled={logout.isPending}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            <LogOut className="h-4 w-4" />
            {logout.isPending ? "Logging out…" : "Log out"}
          </button>
        </div>
      </aside>

      {/* Mobile slide-over sidebar */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setMobileNavOpen(false)}
            aria-hidden="true"
          />
          <aside className="relative flex h-full w-64 flex-col border-r border-gray-200 bg-white py-6">
            <div className="mb-6 flex items-center justify-between px-4">
              <span className="text-lg font-semibold">BookSphere AI</span>
              <button
                onClick={() => setMobileNavOpen(false)}
                aria-label="Close navigation"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            {NavLinks}
            <div className="mt-auto px-3 pt-4">
              <button
                onClick={handleLogout}
                disabled={logout.isPending}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
              >
                <LogOut className="h-4 w-4" />
                {logout.isPending ? "Logging out…" : "Log out"}
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* Main content area */}
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <button
            className="md:hidden"
            onClick={() => setMobileNavOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="hidden md:block" />
          <div className="flex items-center gap-4">
            <OrgSwitcher />
            {user && (
              <span className="hidden text-sm text-gray-600 sm:inline">
                {user.full_name}
              </span>
            )}
          </div>
        </header>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
