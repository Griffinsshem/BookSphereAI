"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useAvailability } from "../hooks/useBookings";

function formatSlotTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
}

function todayIsoDate(): string {
  return new Date().toISOString().split("T")[0];
}

export function SlotPicker({
  organizationId,
  resourceId,
  serviceId,
  selectedSlot,
  onSelectSlot,
}: {
  organizationId: string;
  resourceId: string;
  serviceId: string;
  selectedSlot: string | null;
  onSelectSlot: (isoStartTime: string) => void;
}) {
  const [date, setDate] = useState(todayIsoDate());

  const { data, isLoading, isError } = useAvailability(
    organizationId,
    resourceId,
    serviceId,
    date,
  );

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label htmlFor="booking-date" className="text-sm font-medium">
          Date
        </label>
        <input
          id="booking-date"
          type="date"
          value={date}
          min={todayIsoDate()}
          onChange={(e) => {
            setDate(e.target.value);
            onSelectSlot(""); // clear stale selection when date changes
          }}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      {isLoading && <p className="text-sm text-gray-600">Loading available times…</p>}

      {isError && (
        <p role="alert" className="text-sm text-red-600">
          Couldn&apos;t load availability. Please try again.
        </p>
      )}

      {data && data.available_slots.length === 0 && (
        <p className="text-sm text-gray-600">No available times on this date.</p>
      )}

      {data && data.available_slots.length > 0 && (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
          {data.available_slots.map((slot) => (
            <Button
              key={slot}
              type="button"
              variant={selectedSlot === slot ? "default" : "outline"}
              size="sm"
              aria-pressed={selectedSlot === slot}
              onClick={() => onSelectSlot(slot)}
            >
              {formatSlotTime(slot)}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
