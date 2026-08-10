import { beforeEach, describe, expect, it } from "vitest";
import { useOrgStore } from "@/lib/org-store";

beforeEach(() => {
  useOrgStore.getState().clearCurrentOrg();
});

const orgA = { id: "org-a", name: "Org A", slug: "org-a", role: "owner" };
const orgB = { id: "org-b", name: "Org B", slug: "org-b", role: "staff" };

describe("useOrgStore", () => {
  it("defaults to the first org when none was previously selected", () => {
    useOrgStore.getState().setAvailableOrgs([orgA, orgB]);
    expect(useOrgStore.getState().currentOrg?.id).toBe("org-a");
  });

  it("switchOrg changes the current selection", () => {
    useOrgStore.getState().setAvailableOrgs([orgA, orgB]);
    useOrgStore.getState().switchOrg("org-b");
    expect(useOrgStore.getState().currentOrg?.id).toBe("org-b");
  });

  it("switchOrg ignores an id not in availableOrgs", () => {
    useOrgStore.getState().setAvailableOrgs([orgA, orgB]);
    useOrgStore.getState().switchOrg("nonexistent-org");
    expect(useOrgStore.getState().currentOrg?.id).toBe("org-a"); // unchanged
  });

  it("preserves the current selection across a refetch if still valid", () => {
    useOrgStore.getState().setAvailableOrgs([orgA, orgB]);
    useOrgStore.getState().switchOrg("org-b");

    // Simulates /users/me refetching and returning the same two orgs
    // in a different order -- the user's active selection (org-b)
    // must NOT silently reset back to whatever is first in the list.
    useOrgStore.getState().setAvailableOrgs([orgB, orgA]);

    expect(useOrgStore.getState().currentOrg?.id).toBe("org-b");
  });

  it("falls back to the first org if the previously selected one disappears", () => {
    useOrgStore.getState().setAvailableOrgs([orgA, orgB]);
    useOrgStore.getState().switchOrg("org-b");

    // Simulates being removed from org-b.
    useOrgStore.getState().setAvailableOrgs([orgA]);

    expect(useOrgStore.getState().currentOrg?.id).toBe("org-a");
  });
});
