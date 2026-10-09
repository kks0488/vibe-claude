import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { C, mono as monoEn, monoKo, sans as sansEn, sansKo } from "./theme";

export type Lang = "en" | "ko";
const LangCtx = React.createContext<Lang>("en");
const useLang = () => React.useContext(LangCtx);
const useFonts = () => (useLang() === "ko" ? { sans: sansKo, mono: monoKo } : { sans: sansEn, mono: monoEn });

const COPY = {
  en: {
    title1: "Build with AI without reading code.",
    title2: "And still know it works.",
    chips: ["Proof", "Undo", "Second opinion"],
    proof: "Proof, not promises",
    proofLines: [
      "make the checkout button green",
      "Edit  app/checkout.tsx",
      "Done! The button is green now.",
      "vibe: code changed, nothing ran to check it",
      "Bash  npm test",
      "✓ 24 passed   (real exit code, logged by the hook)",
    ],
    proofReceipt: "vibe ✓ 1 file changed · checked: npm test · undo: /vibe-claude:undo",
    undo: "Nothing is lost",
    undoLines: [
      "clean up the old screenshots",
      "Bash  rm -rf qa/shots",
      "212 files copied to the trash first (kept 7 days)",
      "wait, I needed those. undo",
      "/vibe-claude:undo",
      "✓ 212 files are back. Nothing else changed.",
    ],
    undoReceipt: "vibe ↺ restored 212 files · nothing else changed",
    review: "A second opinion",
    reviewTitle: "codex · independent review",
    reviewLines: [
      "reviewing the change Claude just finished…",
      "calc.py:2  int() drops decimals: add(0.5, 0.25) → 0",
      "Claude: good catch, switching to float() and re-testing",
      "✓ tests pass · Codex: LGTM",
    ],
    reviewReceipt: "vibe ✓ 1 file changed · checked: pytest · reviewed by Codex",
    outro1: "No questions.",
    outro2: "Just proof.",
  },
  ko: {
    title1: "코드를 몰라도 AI로 만들고,",
    title2: "제대로 되는지까지 확인해요.",
    chips: ["증명", "되돌리기", "두 번째 의견"],
    proof: "말 말고, 증거로",
    proofLines: [
      "결제 버튼을 초록색으로 바꿔줘",
      "Edit  app/checkout.tsx",
      "다 했어요! 버튼이 초록색이 됐어요.",
      "vibe: 코드를 바꿨는데 확인한 기록이 없어요",
      "Bash  npm test",
      "✓ 24개 통과   (hook이 기록한 실제 결과)",
    ],
    proofReceipt: "vibe ✓ 파일 1개 변경 · 확인됨: npm test · 되돌리기: /vibe-claude:undo",
    undo: "아무것도 잃지 않아요",
    undoLines: [
      "예전 스크린샷 정리해줘",
      "Bash  rm -rf qa/shots",
      "지우기 전에 파일 212개를 휴지통에 보관했어요 (7일)",
      "아 잠깐, 그거 필요했어. 되돌려줘",
      "/vibe-claude:undo",
      "✓ 파일 212개가 돌아왔어요. 다른 건 그대로예요.",
    ],
    undoReceipt: "vibe ↺ 파일 212개 복구 · 다른 변경 없음",
    review: "다른 AI가 한 번 더",
    reviewTitle: "codex · 독립 검토",
    reviewLines: [
      "Claude가 방금 끝낸 변경을 검토하는 중…",
      "calc.py:2  int()가 소수를 버려요: add(0.5, 0.25) → 0",
      "Claude: 맞네요. float()로 바꾸고 다시 테스트할게요",
      "✓ 테스트 통과 · Codex: 문제 없음",
    ],
    reviewReceipt: "vibe ✓ 파일 1개 변경 · 확인됨: pytest · Codex 검토 완료",
    outro1: "질문은 없이,",
    outro2: "증거만.",
  },
};
const useCopy = () => COPY[useLang()];

// Scene lengths in frames (30 fps).
export const SCENES = { hero: 90, proof: 215, undo: 170, review: 140, outro: 110 };
export const PROMO_FRAMES = Object.values(SCENES).reduce((a, b) => a + b, 0);

const ease = Easing.bezier(0.22, 1, 0.36, 1);

/** Fades a scene in and out at its edges. */
const Scene: React.FC<{ length: number; children: React.ReactNode }> = ({ length, children }) => {
  const f = useCurrentFrame();
  const opacity = interpolate(f, [0, 10, length - 10, length], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ backgroundColor: C.bg, opacity }}>{children}</AbsoluteFill>;
};

const rise = (f: number, at: number, fps: number) => {
  const s = spring({ frame: f - at, fps, config: { damping: 200 } });
  return { opacity: s, transform: `translateY(${(1 - s) * 24}px)` };
};

const Kicker: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => {
  const F = useFonts();
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div
      style={{
        position: "absolute",
        top: 64,
        left: 96,
        fontFamily: F.sans,
        fontWeight: 800,
        fontSize: 64,
        color: C.ink,
        letterSpacing: -1.5,
        ...rise(f, 0, fps),
      }}
    >
      <span style={{ color }}>■ </span>
      {children}
    </div>
  );
};

type Line = { at: number; kind: "you" | "tool" | "say" | "out" | "ok" | "stop" | "warn" | "codex"; text: string; type?: boolean };

const colorOf: Record<Line["kind"], string> = {
  you: C.ink,
  tool: C.ink,
  say: C.ink,
  out: C.dim,
  ok: C.green,
  stop: C.red,
  warn: C.amber,
  codex: C.violet,
};

/** A terminal card whose lines appear (and optionally type out) at given frames. */
const Terminal: React.FC<{ lines: Line[]; top?: number; title?: string }> = ({ lines, top = 170, title = "claude · vibe-claude" }) => {
  const F = useFonts();
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div
      style={{
        position: "absolute",
        top,
        left: 96,
        right: 96,
        background: C.card,
        border: `1px solid ${C.line}`,
        borderRadius: 18,
        padding: "22px 30px 26px",
        boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
        ...rise(f, 4, fps),
      }}
    >
      <div style={{ display: "flex", gap: 9, alignItems: "center", marginBottom: 18 }}>
        {["#ff5f57", "#febc2e", "#28c840"].map((c) => (
          <div key={c} style={{ width: 13, height: 13, borderRadius: 7, background: c }} />
        ))}
        <div style={{ flex: 1, textAlign: "center", fontFamily: F.mono, fontSize: 17, color: C.dim, marginRight: 60 }}>{title}</div>
      </div>
      {lines.map((l, i) => {
        if (f < l.at) return <div key={i} style={{ height: 44 }} />;
        const chars = l.type ? Math.floor(interpolate(f - l.at, [0, l.text.length * 0.9], [0, l.text.length], { extrapolateRight: "clamp" })) : l.text.length;
        const s = spring({ frame: f - l.at, fps, config: { damping: 200 }, durationInFrames: 12 });
        const indent = ["out", "ok", "stop", "warn", "codex"].includes(l.kind);
        const isAlert = l.kind === "stop";
        return (
          <div
            key={i}
            style={{
              height: 44,
              display: "flex",
              alignItems: "center",
              paddingLeft: indent ? 40 : 0,
              fontFamily: F.mono,
              fontSize: 26,
              color: colorOf[l.kind],
              fontWeight: l.kind === "you" || isAlert ? 700 : 400,
              opacity: s,
              transform: `translateX(${(1 - s) * -12}px)`,
            }}
          >
            {l.kind === "you" && <span style={{ color: C.coral, marginRight: 16 }}>›</span>}
            {(l.kind === "tool" || l.kind === "say") && (
              <span style={{ width: 12, height: 12, borderRadius: 6, background: l.kind === "tool" ? C.blue : C.ink, marginRight: 22, display: "inline-block" }} />
            )}
            <span style={{ whiteSpace: "pre", ...(isAlert ? { background: "rgba(255,123,114,0.12)", padding: "2px 10px", borderRadius: 6 } : {}) }}>
              {l.text.slice(0, chars)}
            </span>
          </div>
        );
      })}
    </div>
  );
};

/** The receipt bar that slides up: the one line the user actually reads. */
const Receipt: React.FC<{ at: number; text: string; color?: string }> = ({ at, text, color = C.green }) => {
  const F = useFonts();
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f - at, fps, config: { damping: 14, stiffness: 120 } });
  if (f < at) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: 96,
        right: 96,
        bottom: 56,
        padding: "20px 28px",
        borderRadius: 14,
        background: `${color}22`,
        border: `2px solid ${color}`,
        fontFamily: F.mono,
        fontWeight: 700,
        fontSize: 27,
        color,
        transform: `translateY(${(1 - s) * 80}px) scale(${0.96 + 0.04 * s})`,
        opacity: Math.min(1, s * 1.4),
      }}
    >
      {text}
    </div>
  );
};

const HeroScene: React.FC = () => {
  const F = useFonts();
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(f, [0, SCENES.hero], [1.08, 1.0], { easing: ease });
  const T = useCopy();
  return (
    <Scene length={SCENES.hero}>
      <Img src={staticFile("hero.png")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transform: `translateX(150px) scale(${zoom})` }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(13,17,23,1) 36%, rgba(13,17,23,0) 64%)" }} />
      <div style={{ position: "absolute", left: 96, top: 210, width: 580 }}>
        <div style={{ fontFamily: F.sans, fontWeight: 800, fontSize: 104, color: C.ink, letterSpacing: -4, ...rise(f, 6, fps) }}>
          vibe<span style={{ color: C.coral }}>-</span>claude
        </div>
        <div style={{ fontFamily: F.sans, fontWeight: 600, fontSize: 40, lineHeight: 1.3, color: C.dim, marginTop: 18, ...rise(f, 18, fps) }}>
          {T.title1}
          <br />
          <span style={{ color: C.ink }}>{T.title2}</span>
        </div>
      </div>
    </Scene>
  );
};

const ProofScene: React.FC = () => {
  const T = useCopy();
  const L = T.proofLines;
  return (
    <Scene length={SCENES.proof}>
      <Kicker color={C.green}>{T.proof}</Kicker>
      <Terminal
        lines={[
          { at: 12, kind: "you", text: L[0], type: true },
          { at: 42, kind: "tool", text: L[1] },
          { at: 58, kind: "say", text: L[2], type: true },
          { at: 88, kind: "stop", text: L[3] },
          { at: 118, kind: "tool", text: L[4] },
          { at: 134, kind: "ok", text: L[5] },
        ]}
      />
      <Receipt at={160} text={T.proofReceipt} />
    </Scene>
  );
};

const UndoScene: React.FC = () => {
  const f = useCurrentFrame();
  const spin = interpolate(f, [112, 150], [0, 360], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const show = interpolate(f, [104, 114], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const T = useCopy();
  const L = T.undoLines;
  return (
    <Scene length={SCENES.undo}>
      <Kicker color={C.amber}>{T.undo}</Kicker>
      <Terminal
        lines={[
          { at: 10, kind: "you", text: L[0], type: true },
          { at: 38, kind: "tool", text: L[1] },
          { at: 50, kind: "warn", text: L[2] },
          { at: 82, kind: "you", text: L[3], type: true },
          { at: 108, kind: "tool", text: L[4] },
          { at: 128, kind: "ok", text: L[5] },
        ]}
      />
      <Receipt at={140} color={C.amber} text={T.undoReceipt} />
      <svg width={120} height={120} viewBox="0 0 120 120" style={{ position: "absolute", right: 140, top: 52, opacity: show, transform: `scaleX(-1) rotate(${spin}deg)` }}>
        <path d="M 96 60 A 36 36 0 1 1 74 26" fill="none" stroke={C.coral} strokeWidth={10} strokeLinecap="round" />
        <path d="M 62 10 L 82 26 L 60 40" fill="none" stroke={C.coral} strokeWidth={10} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </Scene>
  );
};

const ReviewScene: React.FC = () => {
  const T = useCopy();
  const L = T.reviewLines;
  return (
    <Scene length={SCENES.review}>
      <Kicker color={C.violet}>{T.review}</Kicker>
      <Terminal
        title={T.reviewTitle}
        lines={[
          { at: 10, kind: "out", text: L[0] },
          { at: 34, kind: "codex", text: L[1] },
          { at: 62, kind: "tool", text: L[2] },
          { at: 88, kind: "ok", text: L[3] },
        ]}
      />
      <Receipt at={100} color={C.violet} text={T.reviewReceipt} />
    </Scene>
  );
};

const OutroScene: React.FC = () => {
  const F = useFonts();
  const T = useCopy();
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <Scene length={SCENES.outro}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 34 }}>
        <div style={{ fontFamily: F.sans, fontWeight: 800, fontSize: 92, color: C.ink, letterSpacing: -3, ...rise(f, 4, fps) }}>
          {T.outro1} <span style={{ color: C.green }}>{T.outro2}</span>
        </div>
        <div
          style={{
            fontFamily: F.mono,
            fontSize: 30,
            color: C.ink,
            background: C.card,
            border: `1px solid ${C.line}`,
            borderRadius: 12,
            padding: "18px 30px",
            ...rise(f, 20, fps),
          }}
        >
          <span style={{ color: C.coral }}>/plugin install</span> vibe-claude@vibe-claude
        </div>
        <div style={{ fontFamily: F.sans, fontSize: 30, color: C.dim, ...rise(f, 32, fps) }}>github.com/kks0488/vibe-claude</div>
      </AbsoluteFill>
    </Scene>
  );
};

export const Promo: React.FC<{ lang: Lang }> = ({ lang }) => {
  let at = 0;
  const seq = (len: number, el: React.ReactNode) => {
    const from = at;
    at += len;
    return (
      <Sequence from={from} durationInFrames={len}>
        {el}
      </Sequence>
    );
  };
  return (
    <LangCtx.Provider value={lang}>
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      {seq(SCENES.hero, <HeroScene />)}
      {seq(SCENES.proof, <ProofScene />)}
      {seq(SCENES.undo, <UndoScene />)}
      {seq(SCENES.review, <ReviewScene />)}
      {seq(SCENES.outro, <OutroScene />)}
    </AbsoluteFill>
    </LangCtx.Provider>
  );
};

/** README banner: the hero illustration with the title set in real type. */
export const Banner: React.FC<{ lang: Lang }> = ({ lang }) => (
  <LangCtx.Provider value={lang}>
    <BannerInner />
  </LangCtx.Provider>
);

const BannerInner: React.FC = () => {
  const F = useFonts();
  const T = useCopy();
  return (
  <AbsoluteFill style={{ backgroundColor: C.bg }}>
    <Img src={staticFile("hero.png")} style={{ position: "absolute", right: -40, top: -150, width: 1500 }} />
    <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(13,17,23,1) 34%, rgba(13,17,23,0) 66%)" }} />
    <div style={{ position: "absolute", left: 90, top: 150, width: 760 }}>
      <div style={{ fontFamily: F.sans, fontWeight: 800, fontSize: 132, color: C.ink, letterSpacing: -5 }}>
        vibe<span style={{ color: C.coral }}>-</span>claude
      </div>
      <div style={{ fontFamily: F.sans, fontWeight: 600, fontSize: 40, lineHeight: 1.3, color: C.dim, marginTop: 12 }}>
        {T.title1}
        <br />
        <span style={{ color: C.ink }}>{T.title2}</span>
      </div>
      <div style={{ display: "flex", gap: 14, marginTop: 34 }}>
        {[
          [T.chips[0], C.green],
          [T.chips[1], C.coral],
          [T.chips[2], C.violet],
        ].map(([label, color]) => (
          <div key={label} style={{ fontFamily: F.sans, fontWeight: 600, fontSize: 26, color, border: `2px solid ${color}`, borderRadius: 999, padding: "8px 22px" }}>
            {label}
          </div>
        ))}
      </div>
    </div>
  </AbsoluteFill>
);
};
