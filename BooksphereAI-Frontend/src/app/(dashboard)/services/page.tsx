"use client";

import { useOrgStore } from "@/lib/org-store";
import { useResources } from "@/features/resources/hooks/useResources";
import { ServiceForm } from "@/features/services/components/ServiceForm";
import { ServiceList } from "@/features/services/components/ServiceList";

export default function ServicesPage() {
  const currentOrg = useOrgStore((s) => s.currentOrg);
  const { data: resourcesData } = useResources(currentOrg?.id);

  if (!currentOrg) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-8">
        <p className="text-sm text-gray-600">Loading your organization…</p>
      </main>
    );
  }

  const canManage = currentOrg.role === "owner" || currentOrg.role === "manager";
  const resources = resourcesData?.items ?? [];

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-semibold">Services</h1>
      <p className="mb-6 text-sm text-gray-600">
        What customers actually book -- linked to one or more resources.
      </p>

      {canManage && (
        <div className="mb-8 rounded-lg border border-gray-200 p-4">
          <h2 className="mb-4 text-lg font-medium">Add a service</h2>
          <ServiceForm organizationId={currentOrg.id} />
        </div>
      )}

      <ServiceList organizationId={currentOrg.id} resources={resources} />
    </main>
  );
}
