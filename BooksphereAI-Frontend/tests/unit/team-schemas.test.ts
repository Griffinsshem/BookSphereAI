import { describe, expect, it } from "vitest";
import { changeRoleSchema, createInviteSchema } from "@/features/team/schemas";

describe("createInviteSchema", () => {
  it("accepts a valid invite", () => {
    const result = createInviteSchema.safeParse({
      email: "someone@example.com",
      role: "staff",
    });
    expect(result.success).toBe(true);
  });

  it("rejects an invalid email", () => {
    const result = createInviteSchema.safeParse({
      email: "not-an-email",
      role: "staff",
    });
    expect(result.success).toBe(false);
  });

  it("rejects 'owner' as a role", () => {
    // owner isn't even in the enum, so this should fail validation
    // -- matches the backend's ASSIGNABLE_ROLES exclusion exactly.
    const result = createInviteSchema.safeParse({
      email: "someone@example.com",
      role: "owner",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an unknown role", () => {
    const result = createInviteSchema.safeParse({
      email: "someone@example.com",
      role: "superadmin",
    });
    expect(result.success).toBe(false);
  });
});

describe("changeRoleSchema", () => {
  it("accepts manager, staff, customer", () => {
    for (const role of ["manager", "staff", "customer"]) {
      expect(changeRoleSchema.safeParse({ role }).success).toBe(true);
    }
  });

  it("rejects owner", () => {
    expect(changeRoleSchema.safeParse({ role: "owner" }).success).toBe(false);
  });
});
