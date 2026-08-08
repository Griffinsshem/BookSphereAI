"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useDeactivateService, useServices } from "../hooks/useServices";
import { ResourceLinker } from "./ResourceLinker";
import type { Resource } from "@/features/resources/api";

function formatPrice(cents: number, currency: string): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
}

export function ServiceList({
  organizationId,
  resources,
}: {
  organizationId: string;
  resources: Resource[];
}) {
  const { data, isLoading, isError } = useServices(organizationId);
  const deactivateService = useDeactivateService(organizationId);
  const [expandedServiceId, setExpandedServiceId] = useState<string | null>(null);

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
        <li key={service.id} className="py-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{service.name}</p>
              <p className="text-sm text-gray-600">
                {service.duration_minutes} min · {formatPrice(service.price_cents, service.currency)}
                {!service.is_active ? " · Inactive" : ""}
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setExpandedServiceId(
                    expandedServiceId === service.id ? null : service.id,
                  )
                }
              >
                {expandedServiceId === service.id ? "Hide resources" : "Manage resources"}
              </Button>
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
            </div>
          </div>
          {expandedServiceId === service.id && (
            <ResourceLinker
              organizationId={organizationId}
              serviceId={service.id}
              resources={resources}
            />
          )}
        </li>
      ))}
    </ul>
  );
}
