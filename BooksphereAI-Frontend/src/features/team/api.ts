import { apiFetch } from "@/lib/api-client";
import type { ChangeRoleFormValues, CreateInviteFormValues } from "./schemas";

export interface Invite {
  id: string;
  organization_id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
  created_at: string;
}

export interface InvitePreview {
  organization_name: string;
  role: string;
  email: string;
  expires_at: string;
}

export interface Member {
  user_id: string;
  role: string;
  email: string;
  full_name: string;
  joined_at: string;
}

export function createInviteRequest(organizationId: string, values: CreateInviteFormValues) {
  return apiFetch<Invite>(`/organizations/${organizationId}/invites`, {
    method: "POST",
    body: JSON.stringify(values),
  });
}

export function listInvitesRequest(organizationId: string) {
  return apiFetch<Invite[]>(`/organizations/${organizationId}/invites`);
}

export function revokeInviteRequest(organizationId: string, inviteId: string) {
  return apiFetch<void>(`/organizations/${organizationId}/invites/${inviteId}`, {
    method: "DELETE",
  });
}

export function previewInviteRequest(token: string) {
  // skipAuth: true -- this endpoint is deliberately public (the
  // token itself is the credential), matching the backend route,
  // which has no @jwt_required() on preview_invite.
  return apiFetch<InvitePreview>(`/invites/${token}`, { skipAuth: true });
}

export function acceptInviteRequest(token: string) {
  return apiFetch<{ organization_id: string; role: string }>(`/invites/${token}/accept`, {
    method: "POST",
  });
}

export function listMembersRequest(organizationId: string) {
  return apiFetch<Member[]>(`/organizations/${organizationId}/members`);
}

export function changeMemberRoleRequest(
  organizationId: string,
  userId: string,
  values: ChangeRoleFormValues,
) {
  return apiFetch<Member>(`/organizations/${organizationId}/members/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(values),
  });
}

export function removeMemberRequest(organizationId: string, userId: string) {
  return apiFetch<void>(`/organizations/${organizationId}/members/${userId}`, {
    method: "DELETE",
  });
}
