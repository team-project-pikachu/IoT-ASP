# UX tooling (Chrome authoring + Apple HIG field UI)

**Authoring browser:** desktop **Chrome**. **Field nodes:** iPhone **Safari**. Constraints: [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md).

## Chosen stack (real repos / products)

| Tool | Role | Source |
|------|------|--------|
| Chrome DevTools | Layout, Performance, Sensors | Chrome |
| Lighthouse | a11y / perf audits | [GoogleChrome/lighthouse](https://github.com/GoogleChrome/lighthouse) |
| axe-core | Accessibility checks | [dequelabs/axe-core](https://github.com/dequelabs/axe-core) |
| Playwright (workspace MCP) | Optional Chrome automation | [microsoft/playwright](https://github.com/microsoft/playwright) |
| Figma (browser / MCP) | Wireframe iteration only | figma-design-ops skill; park if unauthed |
| Awesome indexes | Discovery only | [sindresorhus/awesome](https://github.com/sindresorhus/awesome), [goabstract/Awesome-Design-Tools](https://github.com/goabstract/Awesome-Design-Tools) |
| Xcode + Simulator | Future native shell (#9) | [native-xcode.md](native-xcode.md) |

## Apple HIG (field UI)

- Tap targets ≥ 44 pt; `-apple-system` / SF Pro stack (already in `public/index.html`)
- Monitor / telemetry secondary to blaster content
- See [wireframe-notes.md](wireframe-notes.md), [ux-provenance.md](ux-provenance.md)

Backend sudden-freq → Gemini remains primary; UX is adapt-not-invent.
