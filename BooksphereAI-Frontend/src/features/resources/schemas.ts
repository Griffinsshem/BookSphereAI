/**
 * Mirrors CreateResourceSchema / UpdateResourceSchema /
 * CreateWorkingHoursSchema on the backend.
 */
import { z } from "zod";

export const RESOURCE_TYPES = [
  "room",
  "equipment",
  "vehicle",
  "table",
  "meeting_space",
  "court",
  "medical_device",
  "staff",
  "service_slot",
] as const;

export const createResourceSchema = z.object({
  resourceType: z.enum(RESOURCE_TYPES),
  name: z.string().trim().min(1, "Name is required"),
  description: z.string().trim().optional(),
  capacity: z.coerce.number().int().positive().optional(),
});

export type CreateResourceFormValues = z.infer<typeof createResourceSchema>;

export const createWorkingHoursSchema = z
  .object({
    dayOfWeek: z.coerce.number().int().min(0).max(6),
    startTime: z.string().min(1, "Start time is required"),
    endTime: z.string().min(1, "End time is required"),
  })
  .refine((data) => data.startTime < data.endTime, {
    message: "Start time must be before end time",
    path: ["endTime"],
  });

export type CreateWorkingHoursFormValues = z.infer<typeof createWorkingHoursSchema>;
