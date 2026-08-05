/**
 * Central HTTP client for the BookSphere AI API.
 *
 * Handles three things every single request needs, so no individual
 * feature has to reimplement them:
 *   1. Attaching the access token (Authorization header) and CSRF
 *      token (X-CSRF-Token header, read from the readable csrf cookie).
 *   2. Sending credentials: 'include' so the httpOnly refresh cookie
 *      is sent cross-site (frontend and backend are different domains).
 *   3. Transparently refreshing an expired access token on a 401 and
 *      retrying the original request exactly once.
 */
import { useAuthStore } from "./auth-store";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Reads the CSRF token from the non-httpOnly `bs_csrf_token` cookie.
 * This works specifically because the backend deliberately did NOT
 * mark that cookie httpOnly — see security/csrf.py on the backend for
 * why this pairing (readable CSRF cookie + unreadable refresh cookie)
 * is what makes the double-submit pattern work at all.
 */
function getCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)bs_csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Module-level (not component-level) promise, shared across every
 * caller. Without this, multiple components/requests hitting a 401
 * at the same moment would each independently call /refresh — and
 * because the backend ROTATES the refresh token on every use, the
 * second concurrent refresh call would arrive after the first has
 * already invalidated that cookie's old token, causing it to fail
 * even though the user's session was actually fine. Deduping to a
 * single in-flight refresh avoids this race entirely.
 */
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const csrfToken = getCsrfToken();
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {},
    });

    if (!response.ok) {
      useAuthStore.getState().clearAuth();
      throw new ApiError(response.status, "REFRESH_FAILED", "Session expired");
    }

    const data = (await response.json()) as { access_token: string };
    useAuthStore.getState().setAccessToken(data.access_token);
    return data.access_token;
  })();

  try {
    return await refreshPromise;
  } finally {
    // Cleared whether the refresh succeeded or failed, so the NEXT
    // 401 (a genuinely new one, not a concurrent duplicate) triggers
    // a fresh refresh attempt rather than reusing a resolved promise.
    refreshPromise = null;
  }
}

interface ApiFetchOptions extends RequestInit {
  /** Skip attaching the Authorization header — used for
   * register/login/refresh, which are called before an access token
   * exists. */
  skipAuth?: boolean;
  /** Internal flag: prevents infinite retry loops if the retried
   * request itself somehow gets another 401. */
  _isRetry?: boolean;
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { skipAuth, _isRetry, headers, ...rest } = options;

  const accessToken = useAuthStore.getState().accessToken;
  const csrfToken = getCsrfToken();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(accessToken && !skipAuth
        ? { Authorization: `Bearer ${accessToken}` }
        : {}),
      ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
      ...headers,
    },
  });

  if (response.status === 401 && !skipAuth && !_isRetry) {
    try {
      await refreshAccessToken();
    } catch {
      throw new ApiError(401, "UNAUTHENTICATED", "Please log in again.");
    }
    // Retry the ORIGINAL request once, now with a fresh access token.
    return apiFetch<T>(path, { ...options, _isRetry: true });
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      body?.error?.code ?? "UNKNOWN_ERROR",
      body?.error?.message ?? "Something went wrong. Please try again.",
    );
  }

  return body as T;
}
