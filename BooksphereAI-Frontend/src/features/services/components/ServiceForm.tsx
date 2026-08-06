"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api-client";
import { useCreateService } from "../hooks/useServices";
import { createServiceSchema, type CreateServiceFormValues } from "../schemas";

export function ServiceForm({
  organizationId,
  onCreated,
}: {
  organizationId: string;
  onCreated?: () => void;
}) {
  const createService = useCreateService(organizationId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateServiceFormValues>({
    resolver: zodResolver(createServiceSchema),
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await createService.mutateAsync(values);
      reset();
      onCreated?.();
    } catch {
      // Surfaced via createService.error below.
    }
  });

  const serverError =
    createService.error instanceof ApiError ? createService.error.message : null;

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="svc-name">Name</Label>
        <Input
          id="svc-name"
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? "svc-name-error" : undefined}
          {...register("name")}
        />
        {errors.name && (
          <p id="svc-name-error" role="alert" className="text-sm text-red-600">
            {errors.name.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="svc-description">Description</Label>
        <Input id="svc-description" {...register("description")} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="durationMinutes">Duration (minutes)</Label>
          <Input
            id="durationMinutes"
            type="number"
            min="1"
            max="1440"
            aria-invalid={!!errors.durationMinutes}
            aria-describedby={errors.durationMinutes ? "duration-error" : undefined}
            {...register("durationMinutes")}
          />
          {errors.durationMinutes && (
            <p id="duration-error" role="alert" className="text-sm text-red-600">
              {errors.durationMinutes.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="priceDollars">Price (USD)</Label>
          <Input
            id="priceDollars"
            type="number"
            min="0"
            step="0.01"
            aria-invalid={!!errors.priceDollars}
            aria-describedby={errors.priceDollars ? "price-error" : undefined}
            {...register("priceDollars")}
          />
          {errors.priceDollars && (
            <p id="price-error" role="alert" className="text-sm text-red-600">
              {errors.priceDollars.message}
            </p>
          )}
        </div>
      </div>

      {serverError && (
        <p role="alert" className="text-sm text-red-600">
          {serverError}
        </p>
      )}

      <Button type="submit" disabled={isSubmitting || createService.isPending}>
        {createService.isPending ? "Creating…" : "Create service"}
      </Button>
    </form>
  );
}
