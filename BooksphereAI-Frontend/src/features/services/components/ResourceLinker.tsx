"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useLinkResource } from "../hooks/useServices";
import type { Resource } from "@/features/resources/api";

export function ResourceLinker({
  organizationId,
  serviceId,
  resources,
}: {
  organizationId: string;
  serviceId: string;
  resources: Resource[];
}) {
  const [resourceId, setResourceId] = useState("");
  const linkResource = useLinkResource(organizationId, serviceId);

  const handleLink = async () => {
    if (!resourceId) return;
    try {
      await linkResource.mutateAsync(resourceId);
      setResourceId("");
    } catch {
      // Surfaced via linkResource.error below.
    }
  };

  return (
    <div className="mt-3 space-y-2 border-t border-gray-200 pt-3">
      <p className="text-sm font-medium">Link a resource to this service</p>
      <p className="text-sm text-gray-600">
        A resource must be linked before it can be booked for this service.
      </p>
      <div className="flex items-center gap-2">
        <select
          className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
          value={resourceId}
          onChange={(e) => setResourceId(e.target.value)}
        >
          <option value="">Select a resource…</option>
          {resources.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
        <Button
          type="button"
          size="sm"
          onClick={handleLink}
          disabled={!resourceId || linkResource.isPending}
        >
          {linkResource.isPending ? "Linking…" : "Link"}
        </Button>
      </div>
      {linkResource.isError && (
        <p role="alert" className="text-sm text-red-600">
          Couldn&apos;t link that resource. Please try again.
        </p>
      )}
      {linkResource.isSuccess && (
        <p className="text-sm text-green-700">Linked successfully.</p>
      )}
    </div>
  );
}
