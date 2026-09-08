# Private scientific study — PROTOCOL template (PUBLIC PLACEHOLDERS ONLY)

**Classification:** Copy into gitignored `study/` or private `IoT-ASP-study` and fill locally.
Never commit filled site addresses, neighbor identifiers, or recording URIs to the public
`IoT-ASP` default branch.

## 1. Research question (working)

Characterize near-ultrasonic hop carriers (17–23 kHz Web Audio → BT → Soundcore 2) and
vibration/acoustic routing in a controlled field site, with private archival of multi-node
recordings for later Gemini Enterprise analysis.

## 2. Site (fill privately)

| Role | Value (private only) |
|------|----------------------|
| Apparatus / capture site | `<SITE_ADDRESS>` |
| External acoustic source (neighbor unit) | `<NEIGHBOR_UNIT>` |
| External acoustic source (ambient) | Outside (street / yard / HVAC / traffic) |

## 3. Fleet

| Node | Device | Speaker | Mount | Status |
|------|--------|---------|-------|--------|
| node1 | iPhone 16 | Soundcore 2 | Room A | Active |
| node2 | iPhone 16 | Soundcore 2 | Room B | Active |
| node3 | TBD | Soundcore 2 | Chair-taped | Later |

## 4. Metadata tags (required)

Use opaque codes in private logs. Prefer public vocabulary when exporting scrubbed examples:
`ext_source` ∈ `neighbor_unit` | `outside` | `none`.

```json
{
  "ext_source": "outside",
  "site_code": "SITE",
  "node": "node1",
  "algo": "hop",
  "vib_channel": "none",
  "started_at_utc": "ISO-8601",
  "ended_at_utc": "ISO-8601",
  "notes": "free text — no third-party PII beyond protocol tags"
}
```

Validate with `iot_asp_study.validate_sidecar`.
