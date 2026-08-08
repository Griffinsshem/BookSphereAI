/**
 * Tests the SLOT_UNAVAILABLE -> automatic availability refetch
 * behavior in useCreateBooking's onError handler. This is the
 * specific UX decision this feature is built around: a real,
 * server-proven race condition (see the backend's concurrency test)
 * must trigger an automatic refetch, not just an error message the
 * user has to manually recover from.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useCreateBooking } from "@/features/bookings/hooks/useBookings";
import { useAuthStore } from "@/lib/auth-store";

beforeEach(() => {
  useAuthStore.getState().setAccessToken("test-token");
  vi.unstubAllGlobals();
});

function wrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("useCreateBooking slot-conflict handling", () => {
  it("invalidates the availability query when SLOT_UNAVAILABLE is returned", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({
        error: { code: "SLOT_UNAVAILABLE", message: "This time slot was just taken." },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useCreateBooking("org-1"), {
      wrapper: wrapper(queryClient),
    });

    result.current.mutate({
      resourceId: "550e8400-e29b-41d4-a716-446655440000",
      serviceId: "550e8400-e29b-41d4-a716-446655440001",
      startTime: "2026-12-07T09:00:00Z",
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["availability", "org-1"] }),
    );
  });

  it("does NOT invalidate availability for a different error code", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        error: { code: "BOOKING_IN_PAST", message: "Cannot book a slot in the past." },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useCreateBooking("org-1"), {
      wrapper: wrapper(queryClient),
    });

    result.current.mutate({
      resourceId: "550e8400-e29b-41d4-a716-446655440000",
      serviceId: "550e8400-e29b-41d4-a716-446655440001",
      startTime: "2020-01-01T09:00:00Z",
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    const availabilityInvalidations = invalidateSpy.mock.calls.filter(
      (call) =>
        Array.isArray((call[0] as { queryKey?: unknown[] })?.queryKey) &&
        (call[0] as { queryKey: unknown[] }).queryKey[0] === "availability",
    );
    expect(availabilityInvalidations).toHaveLength(0);
  });
});
