import { apiFetch } from "@/lib/api-client";
import type { LoginFormValues, RegisterFormValues } from "./schemas";

interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

interface AuthResponse {
  user: AuthUser;
  access_token: string;
}

interface Membership {
  role: string;
  organization: { id: string; name: string; slug: string };
}

interface MeResponse {
  user: AuthUser;
  memberships: Membership[];
}

export function registerRequest(values: RegisterFormValues) {
  return apiFetch<AuthResponse>("/auth/register", {
    method: "POST",
    skipAuth: true,
    // Field names translated from camelCase (frontend convention) to
    // snake_case (the backend's marshmallow schema field names) here,
    // in ONE place — so every caller can use idiomatic TS naming
    // without needing to know the wire format.
    body: JSON.stringify({
      email: values.email,
      password: values.password,
      full_name: values.fullName,
      organization_name: values.organizationName,
    }),
  });
}

export function loginRequest(values: LoginFormValues) {
  return apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify(values),
  });
}

export function logoutRequest() {
  return apiFetch<{ message: string }>("/auth/logout", { method: "POST" });
}

export function refreshRequest() {
  return apiFetch<{ access_token: string }>("/auth/refresh", {
    method: "POST",
    skipAuth: true,
  });
}

export function getMeRequest() {
  return apiFetch<MeResponse>("/users/me");
}
