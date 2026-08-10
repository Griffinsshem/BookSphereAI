/**
 * Current-organization state, now a REAL switcher.
 *
 * Grown from Resource Management's deliberately minimal placeholder
 * ("there's only one org, use it") now that Team Management makes
 * multi-org membership actually reachable through the product (via
 * accepting an invite to a second org). The SHAPE from before is
 * preserved -- every feature that reads useOrgStore().currentOrg
 * still works unchanged -- this only ADDS the list + switch
 * capability on top.
 */
import { create } from "zustand";

interface OrgSummary {
  id: string;
  name: string;
  slug: string;
  role: string;
}

interface OrgState {
  currentOrg: OrgSummary | null;
  availableOrgs: OrgSummary[];
  setAvailableOrgs: (orgs: OrgSummary[]) => void;
  switchOrg: (orgId: string) => void;
  clearCurrentOrg: () => void;
}

export const useOrgStore = create<OrgState>((set, get) => ({
  currentOrg: null,
  availableOrgs: [],

  setAvailableOrgs: (orgs) => {
    const { currentOrg } = get();
    // Preserves the current selection across a refetch (e.g. after
    // /users/me re-runs) if it's still in the new list; otherwise
    // defaults to the first org -- matches the original "there's
    // only one, use it" behavior for users who still only belong to
    // one organization.
    const stillValid = currentOrg && orgs.some((o) => o.id === currentOrg.id);
    set({
      availableOrgs: orgs,
      currentOrg: stillValid ? currentOrg : (orgs[0] ?? null),
    });
  },

  switchOrg: (orgId) => {
    const { availableOrgs } = get();
    const target = availableOrgs.find((o) => o.id === orgId);
    if (target) {
      set({ currentOrg: target });
    }
  },

  clearCurrentOrg: () => set({ currentOrg: null, availableOrgs: [] }),
}));
