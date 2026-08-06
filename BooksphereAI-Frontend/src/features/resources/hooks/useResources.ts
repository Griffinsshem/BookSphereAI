"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addWorkingHoursRequest,
  createResourceRequest,
  deactivateResourceRequest,
  listResourcesRequest,
  listWorkingHoursRequest,
} from "../api";
import type { CreateResourceFormValues, CreateWorkingHoursFormValues } from "../schemas";

export function useResources(organizationId: string | undefined, page = 1) {
  return useQuery({
    queryKey: ["resources", organizationId, page],
    queryFn: () => listResourcesRequest(organizationId as string, page),
    enabled: !!organizationId,
  });
}

export function useCreateResource(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: CreateResourceFormValues) =>
      createResourceRequest(organizationId as string, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resources", organizationId] });
    },
  });
}

export function useDeactivateResource(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (resourceId: string) =>
      deactivateResourceRequest(organizationId as string, resourceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resources", organizationId] });
    },
  });
}

export function useWorkingHours(organizationId: string | undefined, resourceId: string | undefined) {
  return useQuery({
    queryKey: ["working-hours", organizationId, resourceId],
    queryFn: () => listWorkingHoursRequest(organizationId as string, resourceId as string),
    enabled: !!organizationId && !!resourceId,
  });
}

export function useAddWorkingHours(organizationId: string | undefined, resourceId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: CreateWorkingHoursFormValues) =>
      addWorkingHoursRequest(organizationId as string, resourceId as string, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["working-hours", organizationId, resourceId] });
    },
  });
}
