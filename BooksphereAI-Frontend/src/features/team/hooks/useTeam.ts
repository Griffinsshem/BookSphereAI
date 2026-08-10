"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  acceptInviteRequest,
  changeMemberRoleRequest,
  createInviteRequest,
  listInvitesRequest,
  listMembersRequest,
  previewInviteRequest,
  removeMemberRequest,
  revokeInviteRequest,
} from "../api";
import type { ChangeRoleFormValues, CreateInviteFormValues } from "../schemas";

export function useInvites(organizationId: string | undefined) {
  return useQuery({
    queryKey: ["invites", organizationId],
    queryFn: () => listInvitesRequest(organizationId as string),
    enabled: !!organizationId,
  });
}

export function useCreateInvite(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: CreateInviteFormValues) =>
      createInviteRequest(organizationId as string, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invites", organizationId] });
    },
  });
}

export function useRevokeInvite(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (inviteId: string) => revokeInviteRequest(organizationId as string, inviteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invites", organizationId] });
    },
  });
}

export function useInvitePreview(token: string | undefined) {
  return useQuery({
    queryKey: ["invite-preview", token],
    queryFn: () => previewInviteRequest(token as string),
    enabled: !!token,
    retry: false,
  });
}

export function useAcceptInvite() {
  return useMutation({
    mutationFn: (token: string) => acceptInviteRequest(token),
  });
}

export function useMembers(organizationId: string | undefined) {
  return useQuery({
    queryKey: ["members", organizationId],
    queryFn: () => listMembersRequest(organizationId as string),
    enabled: !!organizationId,
  });
}

export function useChangeMemberRole(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, values }: { userId: string; values: ChangeRoleFormValues }) =>
      changeMemberRoleRequest(organizationId as string, userId, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", organizationId] });
    },
  });
}

export function useRemoveMember(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => removeMemberRequest(organizationId as string, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", organizationId] });
    },
  });
}
