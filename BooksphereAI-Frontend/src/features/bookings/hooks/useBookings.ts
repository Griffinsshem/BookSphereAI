"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/lib/api-client";
import {
  cancelBookingRequest,
  createBookingRequest,
  getAvailabilityRequest,
  listBookingsRequest,
} from "../api";
import type { CreateBookingFormValues } from "../schemas";

export function useAvailability(
  organizationId: string | undefined,
  resourceId: string | undefined,
  serviceId: string | undefined,
  date: string | undefined,
) {
  return useQuery({
    queryKey: ["availability", organizationId, resourceId, serviceId, date],
    queryFn: () =>
      getAvailabilityRequest(
        organizationId as string,
        resourceId as string,
        serviceId as string,
        date as string,
      ),
    enabled: !!organizationId && !!resourceId && !!serviceId && !!date,
  });
}

export function useCreateBooking(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: CreateBookingFormValues) =>
      createBookingRequest(organizationId as string, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings", organizationId] });
    },
    onError: (error) => {
      // SLOT_UNAVAILABLE specifically means someone else took the
      // slot between the user loading the page and clicking confirm
      // -- a real, tested scenario (see the backend's concurrency
      // test), not a hypothetical. Refetching availability here means
      // the now-stale slot list updates automatically, rather than
      // leaving the user staring at a slot that looks available but
      // isn't -- they'd otherwise have to manually refresh to
      // discover why their retry ALSO fails.
      if (error instanceof ApiError && error.code === "SLOT_UNAVAILABLE") {
        queryClient.invalidateQueries({ queryKey: ["availability", organizationId] });
      }
    },
  });
}

export function useBookingsList(organizationId: string | undefined, page = 1) {
  return useQuery({
    queryKey: ["bookings", organizationId, page],
    queryFn: () => listBookingsRequest(organizationId as string, page),
    enabled: !!organizationId,
  });
}

export function useCancelBooking(organizationId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (bookingId: string) => cancelBookingRequest(organizationId as string, bookingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings", organizationId] });
      // Cancelling frees the slot (proven by the backend's
      // "cancelling frees the slot" test) -- availability should
      // reflect that immediately too.
      queryClient.invalidateQueries({ queryKey: ["availability", organizationId] });
    },
  });
}
