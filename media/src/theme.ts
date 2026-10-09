import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

export const sans = loadInter("normal", { weights: ["400", "600", "800"], subsets: ["latin"] }).fontFamily;
export const mono = loadMono("normal", { weights: ["400", "700"], subsets: ["latin"] }).fontFamily;

export const C = {
  bg: "#0d1117",
  card: "#161b22",
  line: "#30363d",
  ink: "#e6edf3",
  dim: "#8b949e",
  coral: "#d97757",
  green: "#3fb950",
  violet: "#bc8cff",
  red: "#ff7b72",
  blue: "#79c0ff",
  amber: "#d29922",
};

import { loadFont as loadNotoKR } from "@remotion/google-fonts/NotoSansKR";
import { loadFont as loadNanumCoding } from "@remotion/google-fonts/NanumGothicCoding";

export const sansKo = loadNotoKR("normal", { weights: ["400", "700", "900"] }).fontFamily;
export const monoKo = loadNanumCoding("normal", { weights: ["400", "700"] }).fontFamily;
