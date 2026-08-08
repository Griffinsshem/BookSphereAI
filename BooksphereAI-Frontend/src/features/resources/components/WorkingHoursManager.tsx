"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useAddWorkingHours, useWorkingHours } from "../hooks/useResources";

const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function WorkingHoursManager({
  organizationId,
  resourceId,
}: {
  organizationId: string;
  resourceId: string;
}) {
  const { data: windows, isLoading } = useWorkingHours(organizationId, resourceId);
  const addWorkingHours = useAddWorkingHours(organizationId, resourceId);

  const [dayOfWeek, setDayOfWeek] = useState("0");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");

  const handleAdd = async () => {
    try {
      await addWorkingHours.mutateAsync({
        dayOfWeek: Number(dayOfWeek),
        startTime,
        endTime,
      });
    } catch {
      // Surfaced via addWorkingHours.error below.
    }
  };

  return (
    <div className="mt-3 space-y-3 border-t border-gray-200 pt-3">
      <p className="text-sm font-medium">Working hours</p>

      {isLoading && <p className="text-sm text-gray-600">Loading…</p>}

      {windows && windows.length === 0 && (
        <p className="text-sm text-gray-600">
          No working hours set yet — this resource can&apos;t be booked until
          you add at least one.
        </p>
      )}

      {windows && windows.length > 0 && (
        <ul className="space-y-1 text-sm text-gray-700">
          {windows.map((w) => (
            <li key={w.id}>
              {DAY_NAMES[w.day_of_week]}: {w.start_time.slice(0, 5)} – {w.end_time.slice(0, 5)}
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap items-end gap-2">
        <div>
          <Label htmlFor={`day-${resourceId}`}>Day</Label>
          <select
            id={`day-${resourceId}`}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            value={dayOfWeek}
            onChange={(e) => setDayOfWeek(e.target.value)}
          >
            {DAY_NAMES.map((name, i) => (
              <option key={i} value={i}>
                {name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label htmlFor={`start-${resourceId}`}>Start</Label>
          <input
            id={`start-${resourceId}`}
            type="time"
            className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor={`end-${resourceId}`}>End</Label>
          <input
            id={`end-${resourceId}`}
            type="time"
            className="rounded-md border border-gray-300 px-2 py-1 text-sm"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
          />
        </div>
        <Button
          type="button"
          size="sm"
          onClick={handleAdd}
          disabled={addWorkingHours.isPending}
        >
          {addWorkingHours.isPending ? "Adding…" : "Add"}
        </Button>
      </div>

      {addWorkingHours.error instanceof Error && (
        <p role="alert" className="text-sm text-red-600">
          {addWorkingHours.error.message}
        </p>
      )}
    </div>
  );
}
