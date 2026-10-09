import { Composition, Still } from "remotion";
import { Banner, Promo, PROMO_FRAMES } from "./Promo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Promo" component={Promo} defaultProps={{ lang: "en" as const }} durationInFrames={PROMO_FRAMES} fps={30} width={1280} height={720} />
      <Composition id="PromoKo" component={Promo} defaultProps={{ lang: "ko" as const }} durationInFrames={PROMO_FRAMES} fps={30} width={1280} height={720} />
      <Still id="Banner" component={Banner} defaultProps={{ lang: "en" as const }} width={1600} height={640} />
      <Still id="BannerKo" component={Banner} defaultProps={{ lang: "ko" as const }} width={1600} height={640} />
    </>
  );
};
