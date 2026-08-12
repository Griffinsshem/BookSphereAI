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
            <p className="font-mono text-sm font-medium">
              {formatDateTime(booking.start_time)}
            </p>
            <div className="mt-1 flex items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                  booking.status === "cancelled"
                    ? "bg-muted text-muted-foreground"
                    : "bg-success/10 text-success"
                }`}
              >
                {booking.status === "cancelled" ? "Cancelled" : "Confirmed"}
              </span>
              {booking.notes && (
                <span className="text-sm text-muted-foreground">{booking.notes}</span>
              )}
            </div>
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
