/**
 * Mirrors CreateBookingSchema on the backend. Note there is no
 * end_time field here at all -- matching the backend design decision
 * that end_time is ALWAYS server-computed from the service's
 * duration_minutes, never client-supplied.
 */
import { z } from "zod";

export const createBookingSchema = z.object({
  resourceId: z.string().uuid(),
  serviceId: z.string().uuid(),
  startTime: z.string().min(1, "Please select a time"),
  notes: z.string().trim().max(2000).optional(),
});

export type CreateBookingFormValues = z.infer<typeof createBookingSchema>;
