"use client";

import { Button } from "@/components/ui/button";
import { useBookingsList, useCancelBooking } from "../hooks/useBookings";

function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function BookingsList({ organizationId }: { organizationId: string }) {
  const { data, isLoading, isError } = useBookingsList(organizationId);
  const cancelBooking = useCancelBooking(organizationId);

  if (isLoading) {
    return <p className="text-sm text-gray-600">Loading bookings…</p>;
  }

  if (isError) {
    return (
      <p role="alert" className="text-sm text-red-600">
        Couldn&apos;t load bookings. Please try again.
      </p>
    );
  }

  if (!data || data.items.length === 0) {
    return <p className="text-sm text-gray-600">No bookings yet.</p>;
  }

  return (
    <ul className="divide-y divide-gray-200">
      {data.items.map((booking) => (
        <li key={booking.id} className="flex items-center justify-between py-3">
          <div>
            <p className="font-medium">{formatDateTime(booking.start_time)}</p>
            <p className="text-sm text-gray-600">
              {booking.status === "cancelled" ? "Cancelled" : "Confirmed"}
              {booking.notes ? ` · ${booking.notes}` : ""}
            </p>
          </div>
          {booking.status === "confirmed" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => cancelBooking.mutate(booking.id)}
              disabled={cancelBooking.isPending}
            >
              Cancel
            </Button>
          )}
        </li>
      ))}
    </ul>
  );
}
