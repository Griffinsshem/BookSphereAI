/**
 * Mirrors CreateInviteSchema / ChangeRoleSchema on the backend.
 * "owner" deliberately excluded from ASSIGNABLE_ROLES -- matches
 * domain/team/value_objects.py exactly: granting/revoking owner
 * through invites or role-changes isn't supported (ownership
 * transfer is a separate, not-yet-built flow).
 */
import { z } from "zod";

export const ASSIGNABLE_ROLES = ["manager", "staff", "customer"] as const;

export const createInviteSchema = z.object({
  email: z.string().trim().email("Enter a valid email address"),
  role: z.enum(ASSIGNABLE_ROLES),
});

export type CreateInviteFormValues = z.infer<typeof createInviteSchema>;

export const changeRoleSchema = z.object({
  role: z.enum(ASSIGNABLE_ROLES),
});

export type ChangeRoleFormValues = z.infer<typeof changeRoleSchema>;
