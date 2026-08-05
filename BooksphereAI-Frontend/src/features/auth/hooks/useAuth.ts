"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useAuthStore } from "@/lib/auth-store";
import {
  getMeRequest,
  loginRequest,
  logoutRequest,
  refreshRequest,
  registerRequest,
} from "../api";

export function useRegister() {
  const setAccessToken = useAuthStore((s) => s.setAccessToken);
  const setUser = useAuthStore((s) => s.setUser);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: registerRequest,
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}

export function useLogin() {
  const setAccessToken = useAuthStore((s) => s.setAccessToken);
  const setUser = useAuthStore((s) => s.setUser);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: loginRequest,
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}

export function useLogout() {
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: logoutRequest,
    // onSettled (not onSuccess): clear local state regardless of
    // whether the network request itself succeeded — if it failed
    // (e.g. the user is offline), they still clearly intended to log
    // out, and leaving stale auth state in the UI would be worse than
    // a logout call that silently didn't reach the server.
    onSettled: () => {
      clearAuth();
      queryClient.clear();
    },
  });
}

export function useCurrentUser() {
  const accessToken = useAuthStore((s) => s.accessToken);

  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: getMeRequest,
    enabled: !!accessToken,
    retry: false,
  });
}

/**
 * Runs once, on app mount: silently attempts to exchange the
 * httpOnly refresh cookie (if any) for a fresh access token. This is
 * what makes a hard page reload not immediately look "logged out" —
 * without it, accessToken would stay null forever after a refresh,
 * since we deliberately never persist it (see auth-store.ts).
 */
export function useAuthInit() {
  const setAccessToken = useAuthStore((s) => s.setAccessToken);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    refreshRequest()
      .then((data) => setAccessToken(data.access_token))
      .catch(() => clearAuth());
  }, [setAccessToken, clearAuth]);
}
