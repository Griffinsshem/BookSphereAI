"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createServiceRequest,
  deactivateServiceRequest,
  linkResourceRequest,
  listServicesRequest,
} from "../api";
import type { CreateServiceFormValues } from "../schemas";

export function useServices(organizationId: string | undefined, page = 1) {
  return useQuery({
    queryKey: ["services", organizationId, page],
    queryFn: () => listServicesRequest(organizationId as string, page),
    enabled: !!organizationId,
  });
}

export function useCreateService(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: CreateServiceFormValues) =>
      createServiceRequest(organizationId as string, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services", organizationId] });
    },
  });
}

export function useDeactivateService(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (serviceId: string) =>
      deactivateServiceRequest(organizationId as string, serviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services", organizationId] });
    },
  });
}

export function useLinkResource(organizationId: string | undefined, serviceId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (resourceId: string) =>
      linkResourceRequest(organizationId as string, serviceId as string, resourceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services", organizationId] });
    },
  });
}
