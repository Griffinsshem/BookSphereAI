"use client";

import { useOrgStore } from "@/lib/org-store";
import { InviteForm } from "@/features/team/components/InviteForm";
import { InviteList } from "@/features/team/components/InviteList";
import { MemberList } from "@/features/team/components/MemberList";

export default function TeamPage() {
  const currentOrg = useOrgStore((s) => s.currentOrg);

  if (!currentOrg) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-8">
        <p className="text-sm text-gray-600">Loading your organization…</p>
      </main>
    );
  }

  const canManage = currentOrg.role === "owner" || currentOrg.role === "manager";

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-semibold">Team</h1>
      <p className="mb-6 text-sm text-gray-600">
        Invite people to {currentOrg.name} and manage existing members.
      </p>

      {canManage && (
        <div className="mb-8 rounded-lg border border-gray-200 p-4">
          <h2 className="mb-4 text-lg font-medium">Invite someone</h2>
          <InviteForm organizationId={currentOrg.id} />
        </div>
      )}

      {canManage && (
        <div className="mb-8">
          <h2 className="mb-4 text-lg font-medium">Pending invites</h2>
          <InviteList organizationId={currentOrg.id} />
        </div>
      )}

      <h2 className="mb-4 text-lg font-medium">Members</h2>
      <MemberList organizationId={currentOrg.id} canManage={canManage} />
    </main>
  );
}
