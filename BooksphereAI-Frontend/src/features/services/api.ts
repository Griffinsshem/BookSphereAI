import { apiFetch } from "@/lib/api-client";
import type { CreateServiceFormValues } from "./schemas";

export interface Service {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  duration_minutes: number;
  price_cents: number;
  currency: string;
  is_active: boolean;
}

interface PaginatedResponse<T> {
  items: T[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export function listServicesRequest(organizationId: string, page = 1) {
  return apiFetch<PaginatedResponse<Service>>(
    `/organizations/${organizationId}/services?page=${page}`,
  );
}

export function createServiceRequest(organizationId: string, values: CreateServiceFormValues) {
  return apiFetch<Service>(`/organizations/${organizationId}/services`, {
    method: "POST",
    body: JSON.stringify({
      name: values.name,
      description: values.description || undefined,
      duration_minutes: values.durationMinutes,
      // Dollars -> integer cents, rounded to avoid float artifacts
      // like 79.99 * 100 = 7998.999999999999.
      price_cents: Math.round(values.priceDollars * 100),
    }),
  });
}

export function deactivateServiceRequest(organizationId: string, serviceId: string) {
  return apiFetch<void>(`/organizations/${organizationId}/services/${serviceId}`, {
    method: "DELETE",
  });
}

export function linkResourceRequest(organizationId: string, serviceId: string, resourceId: string) {
  return apiFetch<void>(`/organizations/${organizationId}/services/${serviceId}/resources`, {
    method: "POST",
    body: JSON.stringify({ resource_id: resourceId }),
  });
}
