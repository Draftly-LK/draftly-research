import { loadFont as loadPlex } from "@remotion/google-fonts/IBMPlexSans";
import { loadFont as loadSerif } from "@remotion/google-fonts/SourceSerif4";

// Draftly tokens, as specified in the platform's docs/plan.md.
export const C = {
  navy: "#1B3358",
  navyMid: "#0F1F38",
  navyDeep: "#0B1628",
  gold: "#C69436",
  cream: "#F9E8C6",
  amberBorder: "#AD7B24",
  amberText: "#784405",
  ink: "#0F1F38",
  paper: "#F5F7FA",
  white: "#FFFFFF",
  forest: "#2F6B4F",
  muted: "#A7B3C2",
};

export const FPS = 30;

const plex = loadPlex("normal", { weights: ["400", "500", "600"], subsets: ["latin"] });
const serif = loadSerif("normal", { weights: ["600", "700"], subsets: ["latin"] });

export const FONT = {
  ui: plex.fontFamily,
  display: serif.fontFamily,
};
