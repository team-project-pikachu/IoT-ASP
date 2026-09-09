# Chromecast / Google Cast (web sender)

**Live apps:** [hop-ultrasonic.vercel.app](https://hop-ultrasonic.vercel.app) · [hop-ultrasonic-1digital-design.vercel.app](https://hop-ultrasonic-1digital-design.vercel.app)

Optional **Google Cast** output path for the public hop / near-ultrasonic PWA. Primary fleet TX remains **OS system audio** (AirPlay → Sonos Beam Gen 2, or phone A2DP → Soundcore) per [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md). Cast does **not** replace C1 (no Web Bluetooth).

## What shipped (v1)

| Piece | Role |
|-------|------|
| CAF Web Sender (`cast.framework`) | Device picker via `<google-cast-launcher>` |
| Default Media Receiver (`CC1AD845`) | No Cast Developer Console App ID required |
| `/media/us-carrier-19khz.wav` | Same-origin 19 kHz sine (−8 dBFS peak) loaded on session start |
| Playback-rate nudge | Hop target ≈ `f / 19000` on the carrier bed (approximate) |
| Headroom | Cast session sets sink `chromecast` and reuses Beam digital peak **0.40** (−8 dBFS); Cast receiver volume also capped near 0.40 |
| Optional custom receiver | [`/cast-receiver.html`](../public/cast-receiver.html) + `?castAppId=` for true oscillator hops on-device |

Sender logic lives in [`public/cast-sender.js`](../public/cast-sender.js); the blaster bootstraps it from [`public/index.html`](../public/index.html).

## How to use (Vercel)

1. Open the app in **Google Chrome or Microsoft Edge** on desktop (or Android Chrome). Safari / iOS do **not** expose the Cast Web Sender SDK.
2. Prefer **HTTPS** (Vercel prod/preview). Cast discovery requires a secure context.
3. Chrome must have the **Cast / Google Cast** capability available (built-in Cast on desktop Chrome; extension may be required on some builds).
4. Tap the **Cast** icon next to Systems check → pick a Chromecast / Cast-enabled speaker or display.
5. On connect, the sender loads the ultrasonic carrier WAV on the Default Media Receiver. Turn **Signal on** as usual for the local Web Audio hop path; while casting, hop targets also nudge Cast playback rate.
6. Optional query flags:
   - `?audioSink=chromecast` — persist Cast headroom labeling without relying on session auto-set
   - `?castAppId=<APP_ID>` — use a registered custom receiver instead of Default Media Receiver
   - `?castMedia=/media/us-carrier-19khz.wav` — override media URL (must be **HTTPS**, reachable by the Cast device — not `blob:`)

## Headroom / volume

Same policy family as Beam AirPlay ([sonos-beam-gen2-airplay-volume-constraints.md](sonos-beam-gen2-airplay-volume-constraints.md)):

- UI gain stays **100%** (C4).
- Digital / Cast path peak **0.40** (−8 dBFS) so full-scale Web Audio is not stacked into the Cast stack.
- Prefer keeping Cast / speaker hardware volume moderate; raise speaker volume for SPL only after headroom is in place.
- Ultrasonic honesty: Cast hardware / DSP FR is unpublished for 17–23 kHz — treat as experimental (same caveat as Beam).

## Limitations

| Limit | Detail |
|-------|--------|
| Browser | Cast Web Sender is Chrome/Edge (and Chromium) — not Safari/iOS |
| HTTPS | Required for Cast on the open web |
| Default Media Receiver | Plays a **hosted media URL**, not a live `AudioContext` graph. Hop algorithms stay on the OS audio route; Cast gets a carrier bed + rate nudge |
| Custom hop-on-Cast | Needs a Cast Developer Console **Application ID** pointed at `/cast-receiver.html` (allowlist prod + preview origins), then `?castAppId=` or `<meta name="google-cast-app-id">` |
| Allowlisting | Custom receivers must allowlist Vercel origins; Default Media Receiver does not need sender origin registration for basic media load |
| Secrets | No Cast API keys in git. App ID is public configuration (meta / query / `localStorage hop.castAppId`) |

## Files

- `public/index.html` — Cast button, status line, sink `chromecast`, bootstrap
- `public/cast-sender.js` — CAF init, session + `loadMedia`, tone hook
- `public/cast-receiver.html` — optional custom CAF receiver
- `public/media/us-carrier-19khz.wav` — Default Media Receiver payload

## Related

- [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) C1 / C4 / C6
- [sonos-beam-gen2-airplay-volume-constraints.md](sonos-beam-gen2-airplay-volume-constraints.md)
- [architecture-pwa.md](architecture-pwa.md)
- Google: [Integrate Cast SDK (Web Sender)](https://developers.google.com/cast/docs/web_sender/integrate)
