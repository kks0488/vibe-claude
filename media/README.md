# media

Source for the README banner and the promo video, made with [Remotion](https://www.remotion.dev).

```bash
cd media && npm i
npx remotion still Banner out/banner.png          # -> assets/banner.png
npx remotion render Promo out/vibe-claude-promo.mp4
ffmpeg -i out/vibe-claude-promo.mp4 -vf "fps=15,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" out/demo.gif   # -> assets/demo.gif
```

`public/hero.png` was generated with OpenAI Codex image generation. The terminal demos in `assets/demo-*.svg` come from `assets/make_demos.py`.
