"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";
import { useInvitePreview, useAcceptInvite } from "@/features/team/hooks/useTeam";

export default function AcceptInvitePage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const currentUser = useAuthStore((s) => s.user);

  const { data: preview, isLoading, isError, error } = useInvitePreview(params.token);
  const acceptInvite = useAcceptInvite();
  const [accepted, setAccepted] = useState(false);

  const handleAccept = async () => {
    try {
      await acceptInvite.mutateAsync(params.token);
      setAccepted(true);
    } catch {
      // Surfaced via acceptInvite.error below.
    }
  };

  useEffect(() => {
    if (accepted) {
      const timeout = setTimeout(() => router.push("/"), 1500);
      return () => clearTimeout(timeout);
    }
  }, [accepted, router]);

  if (isLoading) {
    return (
      <main className="mx-auto max-w-md px-4 py-12 text-center">
        <p className="text-sm text-gray-600">Loading invite…</p>
      </main>
    );
  }

  if (isError) {
    const message =
      error instanceof ApiError
        ? error.message
        : "This invite link is invalid.";
    return (
      <main className="mx-auto max-w-md px-4 py-12 text-center">
        <h1 className="mb-2 text-xl font-semibold">Invite not available</h1>
        <p role="alert" className="text-sm text-red-600">
          {message}
        </p>
      </main>
    );
  }

  if (!preview) return null;

  if (accepted) {
    return (
      <main className="mx-auto max-w-md px-4 py-12 text-center">
        <h1 className="mb-2 text-xl font-semibold">You&apos;re in!</h1>
        <p className="text-sm text-gray-600">
          You&apos;ve joined {preview.organization_name}. Redirecting…
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-md px-4 py-12 text-center">
      <h1 className="mb-2 text-xl font-semibold">You&apos;ve been invited</h1>
      <p className="mb-6 text-sm text-gray-600">
        Join <strong>{preview.organization_name}</strong> as a{" "}
        <strong>{preview.role}</strong>.
      </p>

      {!accessToken ? (
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            Log in or create an account with <strong>{preview.email}</strong> to accept.
          </p>
          <div className="flex justify-center gap-3">
            <Button onClick={() => router.push(`/login?next=/invites/${params.token}`)}>
              Log in
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push(`/register?next=/invites/${params.token}`)}
            >
              Create account
            </Button>
          </div>
        </div>
      ) : currentUser && currentUser.email !== preview.email ? (
        <p role="alert" className="text-sm text-red-600">
          You&apos;re logged in as {currentUser.email}, but this invite was sent
          to {preview.email}. Log out and sign in with the invited email to
          accept.
        </p>
      ) : (
        <div className="space-y-3">
          <Button onClick={handleAccept} disabled={acceptInvite.isPending}>
            {acceptInvite.isPending ? "Joining…" : "Accept invite"}
          </Button>
          {acceptInvite.error instanceof ApiError && (
            <p role="alert" className="text-sm text-red-600">
              {acceptInvite.error.message}
            </p>
          )}
        </div>
      )}
    </main>
  );
}
