import { apiFetch } from "@/lib/api-client";
import type { CreateBookingFormValues } from "./schemas";

export interface Booking {
  id: string;
  organization_id: string;
  resource_id: string;
  service_id: string;
  customer_id: string;
  start_time: string;
  end_time: string;
  status: "confirmed" | "cancelled";
  cancelled_at: string | null;
  notes: string | null;
  created_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export function getAvailabilityRequest(
  organizationId: string,
  resourceId: string,
  serviceId: string,
  date: string,
) {
  const params = new URLSearchParams({ resource_id: resourceId, service_id: serviceId, date });
  return apiFetch<{ available_slots: string[] }>(
    `/organizations/${organizationId}/bookings/availability?${params}`,
  );
}

export function createBookingRequest(organizationId: string, values: CreateBookingFormValues) {
  return apiFetch<Booking>(`/organizations/${organizationId}/bookings`, {
    method: "POST",
    body: JSON.stringify({
      resource_id: values.resourceId,
      service_id: values.serviceId,
      start_time: values.startTime,
      notes: values.notes || undefined,
    }),
  });
}

export function listBookingsRequest(organizationId: string, page = 1) {
  return apiFetch<PaginatedResponse<Booking>>(`/organizations/${organizationId}/bookings?page=${page}`);
}

export function cancelBookingRequest(organizationId: string, bookingId: string) {
  return apiFetch<Booking>(`/organizations/${organizationId}/bookings/${bookingId}/cancel`, {
    method: "POST",
  });
}
