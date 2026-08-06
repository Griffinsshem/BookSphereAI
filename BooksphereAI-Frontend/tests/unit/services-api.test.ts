import { beforeEach, describe, expect, it, vi } from "vitest";
import { createServiceRequest } from "@/features/services/api";
import { useAuthStore } from "@/lib/auth-store";

beforeEach(() => {
  useAuthStore.getState().setAccessToken("test-token");
  vi.unstubAllGlobals();
});

describe("createServiceRequest", () => {
  it("converts dollars to integer cents without float drift", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ id: "1" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    // 79.99 * 100 in naive floating point can produce 7998.999999999999
    // -- this is exactly the kind of bug that only shows up on
    // specific input values, which is why it needs its own test
    // rather than relying on the "round number" cases above to catch it.
    await createServiceRequest("org-1", {
      name: "Massage",
      durationMinutes: 60,
      priceDollars: 79.99,
    });

    const [, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(options.body as string);

    expect(body.price_cents).toBe(7999);
    expect(Number.isInteger(body.price_cents)).toBe(true);
  });
});
