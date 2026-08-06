import { describe, expect, it } from "vitest";
import { createServiceSchema } from "@/features/services/schemas";

describe("createServiceSchema", () => {
  it("accepts a valid service", () => {
    const result = createServiceSchema.safeParse({
      name: "Massage",
      durationMinutes: 60,
      priceDollars: 80,
    });
    expect(result.success).toBe(true);
  });

  it("rejects zero duration", () => {
    const result = createServiceSchema.safeParse({
      name: "Bad",
      durationMinutes: 0,
      priceDollars: 80,
    });
    expect(result.success).toBe(false);
  });

  it("rejects duration over 24 hours", () => {
    const result = createServiceSchema.safeParse({
      name: "Bad",
      durationMinutes: 1441,
      priceDollars: 80,
    });
    expect(result.success).toBe(false);
  });

  it("rejects a negative price", () => {
    const result = createServiceSchema.safeParse({
      name: "Bad",
      durationMinutes: 60,
      priceDollars: -5,
    });
    expect(result.success).toBe(false);
  });
});
