/**
 * Client-side auth state: the access token and current user.
 *
 * Deliberately NOT using zustand's `persist` middleware. The refresh
 * token lives in an httpOnly cookie specifically so JavaScript can
 * never read it — persisting the access token here (to localStorage
 * or sessionStorage) would partially defeat that: a single XSS
 * vulnerability anywhere in the app could then read a live, usable
 * access token straight out of storage. In-memory-only means a page
 * reload starts from a clean slate; useAuthInit() (see hooks.ts)
 * silently re-establishes the session using the httpOnly cookie.
 */
import { create } from "zustand";

interface AuthUser {
  id: string;
  email: string;
  full_name: string;
}

interface AuthState {
  accessToken: string | null;
  user: AuthUser | null;
  setAccessToken: (token: string) => void;
  setUser: (user: AuthUser) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  setAccessToken: (token) => set({ accessToken: token }),
  setUser: (user) => set({ user }),
  clearAuth: () => set({ accessToken: null, user: null }),
}));
