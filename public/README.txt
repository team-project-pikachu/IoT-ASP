HOP — near-ultrasonic scientific tooling (public)

Live: https://hop-ultrasonic-1digital-design.vercel.app/
Also: https://hop-ultrasonic.vercel.app/
Fleet: Mac Studio / desktop + phones (e.g. iPhone 16 / iPhone 14) → OS system audio → Sonos Beam (Gen 2).
No Web Bluetooth. TX band 17–23 kHz only (10–20 Hz UI removed). Three-node capable.

Fleet
1. Open this public URL on Mac Studio / Safari or Chrome desktop and/or phones (three nodes OK).
2. Pair each node 1:1 via native OS audio (macOS Sound / AirPlay / Control Center; phones via
   native Bluetooth or AirPlay) to a Sonos Beam (Gen 2). No Web Bluetooth, no in-page picker.
3. For max clean level: Web Audio 100%, OS+Sonos volume max, Night Sound / Speech Enhancement /
   Loudness OFF in the Sonos app (see SPEC.md). Sonos does not publish SPL or 17–23 kHz FR.
4. Mode = Blaster / TX (or Carrier only). Tap Signal on so nodes transmit concurrently.
5. Algorithms: hop (default), pulse (AM gate), shriek (chirp bursts). Vib auto optional.
6. PWA: manifest display=standalone; Add to Dock / Home Screen where supported.
7. Monitor: telemetry beacon (device metrics only, no site PII), watchdog, Copy log JSON, Reseed.

Band 17–23 kHz. Expect Sonos/AirPlay DSP roll-off on ultrasonics. Hold / Manual freezes patches.
