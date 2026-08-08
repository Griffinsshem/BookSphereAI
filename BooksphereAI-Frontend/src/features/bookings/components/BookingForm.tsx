"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api-client";
import type { Resource } from "@/features/resources/api";
import type { Service } from "@/features/services/api";
import { useCreateBooking } from "../hooks/useBookings";
import { SlotPicker } from "./SlotPicker";

export function BookingForm({
  organizationId,
  resources,
  services,
  onBooked,
}: {
  organizationId: string;
  resources: Resource[];
  services: Service[];
  onBooked?: () => void;
}) {
  const [resourceId, setResourceId] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [notes, setNotes] = useState("");

  const createBooking = useCreateBooking(organizationId);

  const canSubmit = !!resourceId && !!serviceId && !!selectedSlot;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    try {
      await createBooking.mutateAsync({
        resourceId,
        serviceId,
        startTime: selectedSlot!,
        notes: notes || undefined,
      });
      setSelectedSlot(null);
      setNotes("");
      onBooked?.();
    } catch {
      // Surfaced via createBooking.error below. SLOT_UNAVAILABLE
      // triggers an automatic availability refetch (see
      // useCreateBooking's onError) -- the slot list below will
      // update on its own once that refetch completes.
    }
  };

  const isSlotConflict =
    createBooking.error instanceof ApiError && createBooking.error.code === "SLOT_UNAVAILABLE";
  const genericError =
    createBooking.error instanceof ApiError && !isSlotConflict
      ? createBooking.error.message
      : null;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="booking-resource">Resource</Label>
        <select
          id="booking-resource"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          value={resourceId}
          onChange={(e) => {
            setResourceId(e.target.value);
            setSelectedSlot(null);
          }}
        >
          <option value="">Select a resource…</option>
          {resources.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="booking-service">Service</Label>
        <select
          id="booking-service"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          value={serviceId}
          onChange={(e) => {
            setServiceId(e.target.value);
            setSelectedSlot(null);
          }}
        >
          <option value="">Select a service…</option>
          {services.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.duration_minutes} min)
            </option>
          ))}
        </select>
      </div>

      {resourceId && serviceId && (
        <SlotPicker
          organizationId={organizationId}
          resourceId={resourceId}
          serviceId={serviceId}
          selectedSlot={selectedSlot}
          onSelectSlot={(slot) => setSelectedSlot(slot || null)}
        />
      )}

      <div className="space-y-2">
        <Label htmlFor="booking-notes">Notes (optional)</Label>
        <textarea
          id="booking-notes"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>

      {isSlotConflict && (
        <p role="alert" className="text-sm text-amber-700">
          That time was just booked by someone else. We&apos;ve refreshed the
          available times below — please pick another.
        </p>
      )}
      {genericError && (
        <p role="alert" className="text-sm text-red-600">
          {genericError}
        </p>
      )}

      <Button
        type="button"
        disabled={!canSubmit || createBooking.isPending}
        onClick={handleSubmit}
        className="w-full"
      >
        {createBooking.isPending ? "Booking…" : "Confirm booking"}
      </Button>
    </div>
  );
}
