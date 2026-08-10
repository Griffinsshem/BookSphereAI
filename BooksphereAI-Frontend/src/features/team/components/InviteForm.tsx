"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api-client";
import { useCreateInvite } from "../hooks/useTeam";
import { ASSIGNABLE_ROLES, createInviteSchema, type CreateInviteFormValues } from "../schemas";

export function InviteForm({ organizationId }: { organizationId: string }) {
  const createInvite = useCreateInvite(organizationId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateInviteFormValues>({
    resolver: zodResolver(createInviteSchema),
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await createInvite.mutateAsync(values);
      reset();
    } catch {
      // Surfaced via createInvite.error below.
    }
  });

  const serverError =
    createInvite.error instanceof ApiError ? createInvite.error.message : null;

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="invite-email">Email</Label>
        <Input
          id="invite-email"
          type="email"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? "invite-email-error" : undefined}
          {...register("email")}
        />
        {errors.email && (
          <p id="invite-email-error" role="alert" className="text-sm text-red-600">
            {errors.email.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="invite-role">Role</Label>
        <select
          id="invite-role"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          defaultValue=""
          aria-invalid={!!errors.role}
          {...register("role")}
        >
          <option value="" disabled>
            Select a role…
          </option>
          {ASSIGNABLE_ROLES.map((role) => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </select>
        {errors.role && (
          <p role="alert" className="text-sm text-red-600">
            {errors.role.message}
          </p>
        )}
      </div>

      {serverError && (
        <p role="alert" className="text-sm text-red-600">
          {serverError}
        </p>
      )}

      <Button type="submit" disabled={isSubmitting || createInvite.isPending}>
        {createInvite.isPending ? "Sending invite…" : "Send invite"}
      </Button>
    </form>
  );
}
