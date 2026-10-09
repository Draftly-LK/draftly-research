/** Seconds, edited independently of recording duration. The original intro is fixed. */
export const timing = {intro: 45, problem: 6, people: 6, documents: 8, checklist: 18, research: 7, draft: 7, overview: 5, closing: 3} as const;
export const at = {
  problem: timing.intro,
  people: timing.intro + timing.problem,
  documents: timing.intro + timing.problem + timing.people,
  checklist: timing.intro + timing.problem + timing.people + timing.documents,
  research: timing.intro + timing.problem + timing.people + timing.documents + timing.checklist,
  draft: timing.intro + timing.problem + timing.people + timing.documents + timing.checklist + timing.research,
  overview: timing.intro + timing.problem + timing.people + timing.documents + timing.checklist + timing.research + timing.draft,
  closing: timing.intro + timing.problem + timing.people + timing.documents + timing.checklist + timing.research + timing.draft + timing.overview,
};
export const FILM_SECONDS = at.closing + timing.closing;
