# M3 vibration integration (`feat/m3-vibration-response`)

Worktree: `/Users/machine/apps/IoT-ASP-wt-m3-vib`  
Branch: `feat/m3-vibration-response` (from `origin/main`)

## Sources

| Issue | Worktree | Branch | Role |
|------|----------|--------|------|
| #6 | `IoT-ASP-wt-issue6` | `feat/6-material-channel-select` | Selector/API + arming policy |
| #4 | `IoT-ASP-wt-issue4` | `feat/4-physical-vib` | DeviceMotion → g, gravity EMA, shake→hop |
| #5 | `IoT-ASP-wt-issue5` | `feat/5-acoustic-vib` | Mic hop-band burst ≥12 dB |

Merge order applied: **#6 → #4 → #5** into one `public/index.html` with a single `armPhysical`/`armAcoustic` declaration owned by `#6` `refreshChannelArms`.

## Live HW verify (do not close issues until done)

- [ ] iPhone DeviceMotion permission + shake → hop (physical armed)
- [ ] Mic permission + clap/tap burst → acoustic hop when Vib auto on
- [ ] `materialPreset` table/chair/speaker/handheld rebinds arms correctly
- [ ] Disarm physical → shake ignored; disarm acoustic → burst ignored
