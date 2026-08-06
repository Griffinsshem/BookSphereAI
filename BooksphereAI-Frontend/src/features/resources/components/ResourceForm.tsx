"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api-client";
import { useCreateResource } from "../hooks/useResources";
import { createResourceSchema, RESOURCE_TYPES, type CreateResourceFormValues } from "../schemas";

export function ResourceForm({
  organizationId,
  onCreated,
}: {
  organizationId: string;
  onCreated?: () => void;
}) {
  const createResource = useCreateResource(organizationId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateResourceFormValues>({
    resolver: zodResolver(createResourceSchema),
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await createResource.mutateAsync(values);
      reset();
      onCreated?.();
    } catch {
      // Surfaced via createResource.error below.
    }
  });

  const serverError =
    createResource.error instanceof ApiError ? createResource.error.message : null;

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="resourceType">Type</Label>
        <select
          id="resourceType"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          aria-invalid={!!errors.resourceType}
          aria-describedby={errors.resourceType ? "resourceType-error" : undefined}
          {...register("resourceType")}
        >
          <option value="">Select a type…</option>
          {RESOURCE_TYPES.map((type) => (
            <option key={type} value={type}>
              {type.replace(/_/g, " ")}
            </option>
          ))}
        </select>
        {errors.resourceType && (
          <p id="resourceType-error" role="alert" className="text-sm text-red-600">
            {errors.resourceType.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? "name-error" : undefined}
          {...register("name")}
        />
        {errors.name && (
          <p id="name-error" role="alert" className="text-sm text-red-600">
            {errors.name.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Input id="description" {...register("description")} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="capacity">Capacity (optional)</Label>
        <Input id="capacity" type="number" min="1" {...register("capacity")} />
      </div>

      {serverError && (
        <p role="alert" className="text-sm text-red-600">
          {serverError}
        </p>
      )}

      <Button type="submit" disabled={isSubmitting || createResource.isPending}>
        {createResource.isPending ? "Creating…" : "Create resource"}
      </Button>
    </form>
  );
}
