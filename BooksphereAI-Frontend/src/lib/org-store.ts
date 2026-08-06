/**
 * Minimal current-organization state.
 *
 * DELIBERATELY not a full multi-org switcher. Every user today has
 * exactly one organization membership (created at registration) --
 * there is no UI path yet to join a second org, only our own test
 * helpers touch the DB directly to simulate that. Building a full
 * picker/switcher now would be scope creep into Team Management,
 * which is where "join multiple orgs" actually becomes reachable
 * through the product.
 *
 * The SHAPE of this hook (a single "current org" read by every
 * feature that needs org-scoped API calls) is what should survive
 * once Team Management lands -- only the internals grow from "there's
 * only one, use it" to "let the user pick which one is active."
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
  setCurrentOrg: (org: OrgSummary) => void;
  clearCurrentOrg: () => void;
}

export const useOrgStore = create<OrgState>((set) => ({
  currentOrg: null,
  setCurrentOrg: (org) => set({ currentOrg: org }),
  clearCurrentOrg: () => set({ currentOrg: null }),
}));
