HOP — near-ultrasonic scientific tooling (public)

Fleet (generic)
1. Open this public URL on two phones. Each pairs 1:1 to its own Bluetooth speaker.
2. Optional third node: phone chair-mounted for structure-borne / accelerometer bias.
3. Mode = Blaster / TX (or Carrier only). Tap Signal on so nodes transmit concurrently.
4. Algorithms: hop (default), pulse (AM gate), shriek (chirp bursts). Enable Vib auto to
   switch by vib class (accel → pulse/shriek; acoustic → pulse/hop). Schedules are
   incoherent per Safari tab (independent RNG). Listen is optional debug only.

Band 17–23 kHz. Expect Bluetooth codec + speaker DSP roll-off. Keep output low
(neighbor-safe; default ~8% Web Audio gain).
