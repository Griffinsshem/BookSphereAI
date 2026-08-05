/**
 * Client-side validation, deliberately mirroring the backend's rules
 * (RegisterRequestSchema / is_password_strong_enough in Python) so
 * users get instant feedback without a round-trip — but the backend
 * remains the actual source of truth and re-validates everything
 * regardless of what the client sends.
 */
import { z } from "zod";

export const registerSchema = z.object({
  fullName: z.string().trim().min(1, "Full name is required"),
  organizationName: z.string().trim().min(1, "Organization name is required"),
  email: z.string().trim().email("Enter a valid email address"),
  password: z
    .string()
    .min(12, "Password must be at least 12 characters")
    .regex(/[A-Za-z]/, "Password must include at least one letter")
    .regex(/\d/, "Password must include at least one number"),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
