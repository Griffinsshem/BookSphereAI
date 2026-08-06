"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { useAuthInit, useCurrentUser } from "@/features/auth/hooks/useAuth";

function AuthInitializer() {
  useAuthInit();
  // Populates useOrgStore as a side effect (see useCurrentUser in
  // useAuth.ts) -- calling it here means org context is available
  // app-wide as soon as a session exists, without every page needing
  // to remember to call it itself.
  useCurrentUser();
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            staleTime: 30_000,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthInitializer />
      {children}
    </QueryClientProvider>
  );
}
