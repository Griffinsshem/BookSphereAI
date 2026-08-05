import { describe, expect, it } from "vitest";
import { loginSchema, registerSchema } from "@/features/auth/schemas";

describe("registerSchema", () => {
  it("accepts a valid payload", () => {
    const result = registerSchema.safeParse({
      fullName: "Ada Lovelace",
      organizationName: "Acme Hotel",
      email: "ada@example.com",
      password: "correct-horse-battery-1",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a password under 12 characters", () => {
    const result = registerSchema.safeParse({
      fullName: "Ada",
      organizationName: "Acme",
      email: "ada@example.com",
      password: "short1",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a password with no digit", () => {
    const result = registerSchema.safeParse({
      fullName: "Ada",
      organizationName: "Acme",
      email: "ada@example.com",
      password: "onlylettersnodigits",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = registerSchema.safeParse({
      fullName: "Ada",
      organizationName: "Acme",
      email: "not-an-email",
      password: "correct-horse-battery-1",
    });
    expect(result.success).toBe(false);
  });
});

describe("loginSchema", () => {
  it("rejects an empty password", () => {
    const result = loginSchema.safeParse({
      email: "ada@example.com",
      password: "",
    });
    expect(result.success).toBe(false);
  });
});
