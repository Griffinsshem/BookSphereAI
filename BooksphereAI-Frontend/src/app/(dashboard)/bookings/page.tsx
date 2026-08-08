"use client";

import { useOrgStore } from "@/lib/org-store";
import { useResources } from "@/features/resources/hooks/useResources";
import { useServices } from "@/features/services/hooks/useServices";
import { BookingForm } from "@/features/bookings/components/BookingForm";
import { BookingsList } from "@/features/bookings/components/BookingsList";

export default function BookingsPage() {
  const currentOrg = useOrgStore((s) => s.currentOrg);
  const { data: resourcesData } = useResources(currentOrg?.id);
  const { data: servicesData } = useServices(currentOrg?.id);

  if (!currentOrg) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-8">
        <p className="text-sm text-gray-600">Loading your organization…</p>
      </main>
    );
  }

  const resources = resourcesData?.items ?? [];
  const services = servicesData?.items ?? [];

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-semibold">Bookings</h1>
      <p className="mb-6 text-sm text-gray-600">
        Book a resource, or view and manage existing bookings.
      </p>

      {resources.length === 0 || services.length === 0 ? (
        <p className="mb-8 text-sm text-gray-600">
          You need at least one resource and one linked service before you can
          create a booking. Set those up on the Resources and Services pages
          first.
        </p>
      ) : (
        <div className="mb-8 rounded-lg border border-gray-200 p-4">
          <h2 className="mb-4 text-lg font-medium">New booking</h2>
          <BookingForm organizationId={currentOrg.id} resources={resources} services={services} />
        </div>
      )}

      <h2 className="mb-4 text-lg font-medium">Your bookings</h2>
      <BookingsList organizationId={currentOrg.id} />
    </main>
  );
}
