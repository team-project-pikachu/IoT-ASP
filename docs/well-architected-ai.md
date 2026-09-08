# Well-Architected AI checklist — IoT-ASP

Mapped from skill `gcp-well-architected-ai` + [GCP AI/ML WAF](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml). Public checklist only.

| Pillar | IoT-ASP requirement | Status |
|--------|---------------------|--------|
| **Security** | Private GCS recordings bucket; no keys in git; ADC / Colab userdata only | Required |
| **Security** | Safari public tooling: **SSO / Deployment Protection off** for production blaster (other agent) | Required |
| **Security** | 5-seat Gemini Enterprise; seats/roster private | Required |
| **Privacy** | No street addresses / neighbor IDs in public repo; study in `IoT-ASP-study` | Required |
| **Cost** | Seat-backed Gemini + subscription agents preferred; no metered keys in repo | Required |
| **Reliability** | Local suddenFreq rotate works offline; Gemini patch optional when online | Required |
| **Ops** | Engine `iot-asp-autoroute` on `bear-iot-asp-rec`; ADK stub under `services/autoroute-adk/` | In progress |
| **Responsible AI** | Safety clamps on vol/band/duty; Hold/Manual; literature-cited VHF limits | Required |
| **Connectivity** | Phone TX = native A2DP only ([DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md)) | Locked |

## Citations

- https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/security
- Firecrawl cache: `reference/knowledge-base/raw/gcp-waf-ai-security.md`
- Vercel Deployment Protection (public tooling should not gate production): https://vercel.com/docs/deployment-protection
