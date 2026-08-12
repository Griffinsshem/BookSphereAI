"use client";

import { useState } from "react";
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
            onSelectSlot("");
          }}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:border-ring focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        />
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading available times…</p>}

      {isError && (
        <p role="alert" className="text-sm text-destructive">
          Couldn&apos;t load availability. Please try again.
        </p>
      )}

      {data && data.available_slots.length === 0 && (
        <p className="text-sm text-muted-foreground">No available times on this date.</p>
      )}

      {data && data.available_slots.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.available_slots.map((slot) => {
            const isSelected = selectedSlot === slot;
            return (
              <button
                key={slot}
                type="button"
                aria-pressed={isSelected}
                onClick={() => onSelectSlot(slot)}
                className={`rounded-full border px-4 py-1.5 font-mono text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 ${
                  isSelected
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-accent/40 text-accent-foreground hover:border-primary hover:bg-accent"
                }`}
              >
                {formatSlotTime(slot)}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
