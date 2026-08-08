import { describe, expect, it } from "vitest";
import { createBookingSchema } from "@/features/bookings/schemas";

describe("createBookingSchema", () => {
  it("accepts a valid booking", () => {
    const result = createBookingSchema.safeParse({
      resourceId: "550e8400-e29b-41d4-a716-446655440000",
      serviceId: "550e8400-e29b-41d4-a716-446655440001",
      startTime: "2026-12-07T09:00:00Z",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a non-UUID resourceId", () => {
    const result = createBookingSchema.safeParse({
      resourceId: "not-a-uuid",
      serviceId: "550e8400-e29b-41d4-a716-446655440001",
      startTime: "2026-12-07T09:00:00Z",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an empty startTime", () => {
    const result = createBookingSchema.safeParse({
      resourceId: "550e8400-e29b-41d4-a716-446655440000",
      serviceId: "550e8400-e29b-41d4-a716-446655440001",
      startTime: "",
    });
    expect(result.success).toBe(false);
  });

  it("does not require notes", () => {
    const result = createBookingSchema.safeParse({
      resourceId: "550e8400-e29b-41d4-a716-446655440000",
      serviceId: "550e8400-e29b-41d4-a716-446655440001",
      startTime: "2026-12-07T09:00:00Z",
    });
    expect(result.success).toBe(true);
  });
});
