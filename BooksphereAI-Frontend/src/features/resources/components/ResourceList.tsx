"use client";

import { Button } from "@/components/ui/button";
import { useDeactivateResource, useResources } from "../hooks/useResources";

export function ResourceList({ organizationId }: { organizationId: string }) {
  const { data, isLoading, isError } = useResources(organizationId);
  const deactivateResource = useDeactivateResource(organizationId);

  if (isLoading) {
    return <p className="text-sm text-gray-600">Loading resources…</p>;
  }

  if (isError) {
    return (
      <p role="alert" className="text-sm text-red-600">
        Couldn&apos;t load resources. Please try again.
      </p>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <p className="text-sm text-gray-600">
        No resources yet. Create one above to get started.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-gray-200">
      {data.items.map((resource) => (
        <li key={resource.id} className="flex items-center justify-between py-3">
          <div>
            <p className="font-medium">{resource.name}</p>
            <p className="text-sm text-gray-600">
              {resource.resource_type.replace(/_/g, " ")}
              {resource.capacity ? ` · Capacity ${resource.capacity}` : ""}
              {!resource.is_active ? " · Inactive" : ""}
            </p>
          </div>
          {resource.is_active && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => deactivateResource.mutate(resource.id)}
              disabled={deactivateResource.isPending}
            >
              Deactivate
            </Button>
          )}
        </li>
      ))}
    </ul>
  );
}
