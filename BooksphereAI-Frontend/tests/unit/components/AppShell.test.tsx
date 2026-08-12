import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AppShell } from "@/components/shared/AppShell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/resources",
  useRouter: () => ({ push: vi.fn() }),
}));

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

beforeEach(() => {
  vi.unstubAllGlobals();
});

describe("AppShell", () => {
  it("renders all five nav links", () => {
    renderWithQueryClient(<AppShell>content</AppShell>);

    for (const label of ["Dashboard", "Resources", "Services", "Bookings", "Team"]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
  });

  it("highlights the active link based on the current path", () => {
    renderWithQueryClient(<AppShell>content</AppShell>);

    // Two copies of each link exist (desktop sidebar + mobile
    // slide-over) -- check at least one "Resources" link has the
    // active styling, matching the mocked pathname "/resources".
    // Checks for "border-primary" (the left accent bar) rather than
    // a specific background color -- ties the test to the SEMANTIC
    // active-state mechanism (the design-token-driven accent), not
    // one specific implementation of it, so a future palette tweak
    // doesn't require touching this test again.
    const resourcesLinks = screen.getAllByText("Resources");
    const activeLink = resourcesLinks.find((el) =>
      el.closest("a")?.className.includes("border-primary"),
    );
    expect(activeLink).toBeDefined();
  });

  it("renders the page content passed as children", () => {
    renderWithQueryClient(<AppShell>Unique Test Content Marker</AppShell>);
    expect(screen.getByText("Unique Test Content Marker")).toBeInTheDocument();
  });
});
