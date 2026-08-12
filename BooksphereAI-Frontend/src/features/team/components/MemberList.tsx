"use client";

import { Button } from "@/components/ui/button";
import { ASSIGNABLE_ROLES } from "../schemas";
import { useChangeMemberRole, useMembers, useRemoveMember } from "../hooks/useTeam";

export function MemberList({
  organizationId,
  canManage,
}: {
  organizationId: string;
  canManage: boolean;
}) {
  const { data, isLoading, isError } = useMembers(organizationId);
  const changeMemberRole = useChangeMemberRole(organizationId);
  const removeMember = useRemoveMember(organizationId);

  if (isLoading) {
    return <p className="text-sm text-gray-600">Loading team members…</p>;
  }

  if (isError) {
    return (
      <p role="alert" className="text-sm text-red-600">
        Couldn&apos;t load members. Please try again.
      </p>
    );
  }

  if (!data || data.length === 0) {
    return <p className="text-sm text-gray-600">No members yet.</p>;
  }

  return (
    <ul className="divide-y divide-gray-200">
      {data.map((member) => {
        // The owner's role/membership can never be changed here --
        // mirrors the backend's CannotModifyOwnerRoleError guard.
        // Hiding the controls rather than showing them disabled is
        // deliberate: a disabled dropdown/button implies "you could
        // do this under some condition," which isn't true here.
        const isOwner = member.role === "owner";

        return (
          <li key={member.user_id} className="flex items-center justify-between py-3">
            <div>
              <p className="font-medium">{member.full_name}</p>
              <p className="text-sm text-gray-600">{member.email}</p>
            </div>
            <div className="flex items-center gap-2">
              {isOwner || !canManage ? (
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                    isOwner
                      ? "bg-accent text-accent-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {member.role}
                </span>
              ) : (
                <>
                  <select
                    aria-label={`Change role for ${member.full_name}`}
                    className="rounded-md border border-gray-300 px-2 py-1 text-sm"
                    value={member.role}
                    onChange={(e) =>
                      changeMemberRole.mutate({
                        userId: member.user_id,
                        values: { role: e.target.value as (typeof ASSIGNABLE_ROLES)[number] },
                      })
                    }
                  >
                    {ASSIGNABLE_ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => removeMember.mutate(member.user_id)}
                    disabled={removeMember.isPending}
                  >
                    Remove
                  </Button>
                </>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
