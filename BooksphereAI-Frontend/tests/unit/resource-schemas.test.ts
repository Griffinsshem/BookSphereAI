import { describe, expect, it } from "vitest";
import { createResourceSchema, createWorkingHoursSchema } from "@/features/resources/schemas";

describe("createResourceSchema", () => {
  it("accepts a valid resource", () => {
    const result = createResourceSchema.safeParse({
      resourceType: "room",
      name: "Massage Room 1",
    });
    expect(result.success).toBe(true);
  });

  it("rejects an unknown resource type", () => {
    const result = createResourceSchema.safeParse({
      resourceType: "spaceship",
      name: "Nope",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an empty name", () => {
    const result = createResourceSchema.safeParse({
      resourceType: "room",
      name: "   ",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a non-positive capacity", () => {
    const result = createResourceSchema.safeParse({
      resourceType: "table",
      name: "Table 1",
      capacity: 0,
    });
    expect(result.success).toBe(false);
  });
});

describe("createWorkingHoursSchema", () => {
  it("accepts a valid window", () => {
    const result = createWorkingHoursSchema.safeParse({
      dayOfWeek: 0,
      startTime: "09:00",
      endTime: "17:00",
    });
    expect(result.success).toBe(true);
  });

  it("rejects end time before start time", () => {
    const result = createWorkingHoursSchema.safeParse({
      dayOfWeek: 0,
      startTime: "17:00",
      endTime: "09:00",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a day out of range", () => {
    const result = createWorkingHoursSchema.safeParse({
      dayOfWeek: 7,
      startTime: "09:00",
      endTime: "17:00",
    });
    expect(result.success).toBe(false);
  });
});
