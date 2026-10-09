// Team media. Drop files into public/audio and public/camera, then name them
// here and re-render. Anything left null shows a labelled placeholder instead.
//
// audio:  that section's narration, read by its narrator (mp3 or wav).
// camera: a short clip of the narrator on camera (mp4), shown picture-in-picture
//         for the first seconds of their first section and in the closing credits.

export interface SectionMedia {
  audio: string | null;
}

export const SECTION_MEDIA: Record<string, SectionMedia> = {
  problem: { audio: null }, // e.g. "audio/01-problem-praveen.mp3"
  intro: { audio: null },
  matter: { audio: null },
  process: { audio: null },
  verify: { audio: null },
  checks: { audio: null },
  research: { audio: null },
  draft: { audio: null },
  approve: { audio: null },
  record: { audio: null },
  closing: { audio: null },
};

export const CAMERA: Record<"Praveen" | "Himath" | "Lahiru", string | null> = {
  Praveen: null, // e.g. "camera/praveen.mp4"
  Himath: null,
  Lahiru: null,
};

// Case-law clip recorded on the hosted site with OBS (local search needs the
// retrieval service). Set to e.g. "footage/case-law-live.mp4".
export const CASE_LAW_CLIP: string | null = null;

// Optional music bed, kept quiet under the narration.
export const MUSIC: string | null = null; // e.g. "audio/music.mp3"

export const TEAM = [
  { name: "Himath Dhanapala", role: "Document AI, retrieval and drafting", key: "Himath" as const },
  { name: "Praveen De Silva", role: "Lawyer workflow, interface and testing", key: "Praveen" as const },
  { name: "Lahiru Dilshan", role: "Case law, security and deployment", key: "Lahiru" as const },
];

// Burned-in subtitles. Set to false to hide them (e.g. once narration is added
// and you would rather use YouTube's own captions).
export const SHOW_CAPTIONS = true;

// The lawyers consulted (section 2). Put each photo in public/lawyers/ and list
// it here, in the order you want them shown. A square or portrait head-and-
// shoulders photo works best (jpg or png). Leave `photo` null to keep the
// placeholder icon. `caption` is optional (e.g. "Notary Public"); only add a
// name or caption the person has agreed to.
export interface Lawyer {
  photo: string | null; // e.g. "lawyers/lawyer-1.jpg"
  caption?: string;
}

export const LAWYERS: Lawyer[] = [
  { photo: "lawyers/lawyer-1.jpeg" },
  { photo: "lawyers/lawyer-2.jpeg" },
  { photo: "lawyers/lawyer-3.jpeg" },
  { photo: "lawyers/lawyer-4.jpeg" },
];
