HOP — near-ultrasonic scientific tooling (public)

Live: https://hop-ultrasonic-1digital-design.vercel.app/
Fleet: 3 phones — 2× iPhone 16 + 1× iPhone 14, each 1:1 to its own Soundcore 2 over
iOS native Bluetooth (A2DP). No Web Bluetooth.

Fleet (generic)
1. Open this public URL on the fleet phones (three). Each pairs 1:1 to its own Bluetooth speaker
   via the iOS system audio route (Settings / Control Center). No Web Bluetooth, no in-page picker.
2. Optional third role: phone chair-mounted for structure-borne / accelerometer bias.
3. Mode = Blaster / TX (or Carrier only). Tap Signal on so nodes transmit concurrently.
4. Algorithms: hop (default), pulse (AM gate), shriek (chirp bursts). Enable Vib auto to
   switch by vib class (accel → pulse/shriek; acoustic → pulse/hop). Schedules are
   incoherent per Safari tab (per-device entropy-mixed seed → mulberry32; Reseed button
   in the Monitor section re-rolls it). Listen is optional debug only.
5. Monitor section: telemetry beacon (device metrics only, no site PII), hop age / ctx
   resumes / watchdog counters, Copy log JSON (structured log tail), Reseed.

Band 17–23 kHz. Expect Bluetooth codec + speaker DSP roll-off. Keep output low
(neighbor-safe; default ~8% Web Audio gain). Hold / Manual freezes remote param patches.
