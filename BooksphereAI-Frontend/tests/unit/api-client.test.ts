import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";

function mockFetchSequence(...responses: Array<Partial<Response> & { jsonBody?: unknown }>) {
  const fn = vi.fn();
  for (const r of responses) {
    fn.mockResolvedValueOnce({
      ok: r.ok ?? true,
      status: r.status ?? 200,
      json: async () => r.jsonBody ?? {},
    } as Response);
  }
  vi.stubGlobal("fetch", fn);
  return fn;
}

beforeEach(() => {
  useAuthStore.getState().clearAuth();
  document.cookie = "bs_csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
  vi.unstubAllGlobals();
});

describe("apiFetch", () => {
  it("attaches the access token as a Bearer header when present", async () => {
    useAuthStore.getState().setAccessToken("test-token-123");
    const fetchMock = mockFetchSequence({ ok: true, jsonBody: { ok: true } });

    await apiFetch("/some/path");

    const [, options] = fetchMock.mock.calls[0];
    expect((options.headers as Record<string, string>).Authorization).toBe(
      "Bearer test-token-123",
    );
  });

  it("does not attach Authorization when skipAuth is true", async () => {
    useAuthStore.getState().setAccessToken("test-token-123");
    const fetchMock = mockFetchSequence({ ok: true, jsonBody: { ok: true } });

    await apiFetch("/auth/login", { skipAuth: true });

    const [, options] = fetchMock.mock.calls[0];
    expect((options.headers as Record<string, string>).Authorization).toBeUndefined();
  });

  it("throws ApiError with the server's error code/message on failure", async () => {
    mockFetchSequence({
      ok: false,
      status: 409,
      jsonBody: { error: { code: "EMAIL_TAKEN", message: "Email already registered." } },
    });

    await expect(apiFetch("/auth/register", { skipAuth: true })).rejects.toMatchObject({
      status: 409,
      code: "EMAIL_TAKEN",
      message: "Email already registered.",
    });
  });

  it("on a 401, refreshes the token once and retries the original request", async () => {
    document.cookie = "bs_csrf_token=test-csrf";
    useAuthStore.getState().setAccessToken("expired-token");

    const fetchMock = mockFetchSequence(
      { ok: false, status: 401, jsonBody: { error: { code: "TOKEN_EXPIRED" } } },
      { ok: true, status: 200, jsonBody: { access_token: "fresh-token" } },
      { ok: true, status: 200, jsonBody: { data: "the real payload" } },
    );

    const result = await apiFetch<{ data: string }>("/users/me");

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(result).toEqual({ data: "the real payload" });
    expect(useAuthStore.getState().accessToken).toBe("fresh-token");

    const retryCall = fetchMock.mock.calls[2];
    expect((retryCall[1].headers as Record<string, string>).Authorization).toBe(
      "Bearer fresh-token",
    );
  });

  it("clears auth state if the refresh itself fails", async () => {
    useAuthStore.getState().setAccessToken("expired-token");
    useAuthStore.getState().setUser({ id: "1", email: "a@b.com", full_name: "A" });

    mockFetchSequence(
      { ok: false, status: 401, jsonBody: { error: { code: "TOKEN_EXPIRED" } } },
      { ok: false, status: 401, jsonBody: { error: { code: "INVALID_REFRESH_TOKEN" } } },
    );

    await expect(apiFetch("/users/me")).rejects.toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });
});
