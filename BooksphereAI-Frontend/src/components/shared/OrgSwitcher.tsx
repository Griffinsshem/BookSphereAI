"use client";

import { useOrgStore } from "@/lib/org-store";

/**
 * Renders as a plain label (not a dropdown) when the user belongs to
 * only one organization -- the common case, and showing an
 * interactive picker with a single, unchangeable option would be
 * confusing UI, not helpful UI.
 */
export function OrgSwitcher() {
  const currentOrg = useOrgStore((s) => s.currentOrg);
  const availableOrgs = useOrgStore((s) => s.availableOrgs);
  const switchOrg = useOrgStore((s) => s.switchOrg);

  if (!currentOrg) return null;

  if (availableOrgs.length <= 1) {
    return (
      <span className="text-sm font-medium text-gray-700">{currentOrg.name}</span>
    );
  }

  return (
    <select
      aria-label="Switch organization"
      className="rounded-md border border-gray-300 px-2 py-1 text-sm font-medium"
      value={currentOrg.id}
      onChange={(e) => switchOrg(e.target.value)}
    >
      {availableOrgs.map((org) => (
        <option key={org.id} value={org.id}>
          {org.name} ({org.role})
        </option>
      ))}
    </select>
  );
}
