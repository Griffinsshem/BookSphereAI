"use client";

import { Button } from "@/components/ui/button";
import { useInvites, useRevokeInvite } from "../hooks/useTeam";

export function InviteList({ organizationId }: { organizationId: string }) {
  const { data, isLoading, isError } = useInvites(organizationId);
  const revokeInvite = useRevokeInvite(organizationId);

  if (isLoading) {
    return <p className="text-sm text-gray-600">Loading pending invites…</p>;
  }

  if (isError) {
    return (
      <p role="alert" className="text-sm text-red-600">
        Couldn&apos;t load invites. Please try again.
      </p>
    );
  }

  if (!data || data.length === 0) {
    return <p className="text-sm text-gray-600">No pending invites.</p>;
  }

  return (
    <ul className="divide-y divide-gray-200">
      {data.map((invite) => (
        <li key={invite.id} className="flex items-center justify-between py-3">
          <div>
            <p className="font-medium">{invite.email}</p>
            <div className="mt-1 flex items-center gap-2">
              <span className="inline-flex items-center rounded-full bg-warning/10 px-2 py-0.5 text-xs font-medium capitalize text-warning">
                {invite.role}
              </span>
              <span className="font-mono text-xs text-muted-foreground">
                Expires {new Date(invite.expires_at).toLocaleDateString()}
              </span>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => revokeInvite.mutate(invite.id)}
            disabled={revokeInvite.isPending}
          >
            Revoke
          </Button>
        </li>
      ))}
    </ul>
  );
}
