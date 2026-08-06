import { z } from "zod";

export const createServiceSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  description: z.string().trim().optional(),
  durationMinutes: z.coerce.number().int().min(1).max(1440),
  // Entered as dollars in the UI, converted to cents before sending --
  // keeps the form human-friendly while the wire format stays exact.
  priceDollars: z.coerce.number().min(0),
});

export type CreateServiceFormValues = z.infer<typeof createServiceSchema>;
