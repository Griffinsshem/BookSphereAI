"use client";

import { Button } from "@/components/ui/button";
import { useDeactivateService, useServices } from "../hooks/useServices";

function formatPrice(cents: number, currency: string): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
}

export function ServiceList({ organizationId }: { organizationId: string }) {
  const { data, isLoading, isError } = useServices(organizationId);
  const deactivateService = useDeactivateService(organizationId);

  if (isLoading) {
    return <p className="text-sm text-gray-600">Loading services…</p>;
  }

  if (isError) {
    return (
      <p role="alert" className="text-sm text-red-600">
        Couldn&apos;t load services. Please try again.
      </p>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <p className="text-sm text-gray-600">No services yet. Create one above to get started.</p>
    );
  }

  return (
    <ul className="divide-y divide-gray-200">
      {data.items.map((service) => (
        <li key={service.id} className="flex items-center justify-between py-3">
          <div>
            <p className="font-medium">{service.name}</p>
            <p className="text-sm text-gray-600">
              {service.duration_minutes} min · {formatPrice(service.price_cents, service.currency)}
              {!service.is_active ? " · Inactive" : ""}
            </p>
          </div>
          {service.is_active && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => deactivateService.mutate(service.id)}
              disabled={deactivateService.isPending}
            >
              Deactivate
            </Button>
          )}
        </li>
      ))}
    </ul>
  );
}
