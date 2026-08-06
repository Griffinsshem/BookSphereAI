import { apiFetch } from "@/lib/api-client";
import type { CreateResourceFormValues, CreateWorkingHoursFormValues } from "./schemas";

export interface Resource {
  id: string;
  organization_id: string;
  resource_type: string;
  user_id: string | null;
  name: string;
  description: string | null;
  capacity: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkingHoursWindow {
  id: string;
  resource_id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

interface PaginatedResponse<T> {
  items: T[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export function listResourcesRequest(organizationId: string, page = 1) {
  return apiFetch<PaginatedResponse<Resource>>(
    `/organizations/${organizationId}/resources?page=${page}`,
  );
}

export function createResourceRequest(organizationId: string, values: CreateResourceFormValues) {
  return apiFetch<Resource>(`/organizations/${organizationId}/resources`, {
    method: "POST",
    body: JSON.stringify({
      resource_type: values.resourceType,
      name: values.name,
      description: values.description || undefined,
      capacity: values.capacity,
    }),
  });
}

export function deactivateResourceRequest(organizationId: string, resourceId: string) {
  return apiFetch<void>(`/organizations/${organizationId}/resources/${resourceId}`, {
    method: "DELETE",
  });
}

export function listWorkingHoursRequest(organizationId: string, resourceId: string) {
  return apiFetch<WorkingHoursWindow[]>(
    `/organizations/${organizationId}/resources/${resourceId}/working-hours`,
  );
}

export function addWorkingHoursRequest(
  organizationId: string,
  resourceId: string,
  values: CreateWorkingHoursFormValues,
) {
  return apiFetch<WorkingHoursWindow>(
    `/organizations/${organizationId}/resources/${resourceId}/working-hours`,
    {
      method: "POST",
      body: JSON.stringify({
        day_of_week: values.dayOfWeek,
        start_time: values.startTime,
        end_time: values.endTime,
      }),
    },
  );
}
