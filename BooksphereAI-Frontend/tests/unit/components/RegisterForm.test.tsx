import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RegisterForm } from "@/features/auth/components/RegisterForm";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.unstubAllGlobals();
});

describe("RegisterForm", () => {
  it("shows validation errors for empty required fields on submit", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);

    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findAllByRole("alert")).not.toHaveLength(0);
    expect(screen.getByText(/full name is required/i)).toBeInTheDocument();
  });

  it("shows a specific error for a weak password", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);

    await user.type(screen.getByLabelText(/password/i), "short1");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(
      await screen.findByText(/at least 12 characters/i),
    ).toBeInTheDocument();
  });

  it("submits successfully with valid input", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({
        user: { id: "1", email: "ada@example.com", full_name: "Ada Lovelace" },
        access_token: "new-token",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderWithQueryClient(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), "Ada Lovelace");
    await user.type(screen.getByLabelText(/organization name/i), "Acme Hotel");
    await user.type(screen.getByLabelText(/^email$/i), "ada@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "correct-horse-battery-1");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("/auth/register");
  });
});
