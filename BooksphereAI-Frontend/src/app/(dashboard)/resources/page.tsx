"use client";

import { useOrgStore } from "@/lib/org-store";
import { ResourceForm } from "@/features/resources/components/ResourceForm";
import { ResourceList } from "@/features/resources/components/ResourceList";

export default function ResourcesPage() {
  const currentOrg = useOrgStore((s) => s.currentOrg);

  if (!currentOrg) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-8">
        <p className="text-sm text-gray-600">Loading your organization…</p>
      </main>
    );
  }

  const canManage = currentOrg.role === "owner" || currentOrg.role === "manager";

  return (
    <main className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-semibold">Resources</h1>
      <p className="mb-6 text-sm text-gray-600">
        Rooms, equipment, staff, and anything else your organization books.
      </p>

      {canManage && (
        <div className="mb-8 rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-medium">Add a resource</h2>
          <ResourceForm organizationId={currentOrg.id} />
        </div>
      )}

      <ResourceList organizationId={currentOrg.id} />
    </main>
  );
}
