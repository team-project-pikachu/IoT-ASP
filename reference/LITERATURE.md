# Literature pull — IoT-ASP (Lane C)

**Pull date:** 2026-09-07 (America/New_York).  
**Corpora:** arXiv API, PubMed (NCBI E-utilities), ClinicalTrials.gov API v2, Firecrawl research paper index, mandated publisher abstract pages.  
**Policy:** Prefer recent (2023–2026) plus seminal older. **No fabricated citations.** Paywall → **abstract + DOI/PMID only**. No site addresses in this public file.

Raw exports: `reference/research/raw/` (`arxiv-*`, `pubmed-*`, `clinicaltrials-hits.json`, `fc-*.json`, `jasa-scrape.md`, `pain-scrape.md`).

Private study tree (`IoT-ASP-study`) may hold address-bearing notes; **this file stays generic**.

---

## Queries used

| Corpus | Query / term |
|--------|----------------|
| arXiv | `ti:infrasound OR abs:infrasound`; near-ultrasonic / ultrasonic+smartphone; structure-borne / WBV |
| arXiv | `very high-frequency sound` OR `airborne ultrasound` OR `near-ultrasonic` (newest) |
| PubMed | infrasound perception/annoyance; seated WBV / human–seat; VHFS/ultrasound human |
| CT.gov | `infrasound` (exposure-relevant subset) |
| Firecrawl research | infrasound felt &lt;20 Hz; VHFS/US human effects; pulsed ultrasonic; structure-borne seat |

---

## Mandated publisher pulls

### 1. JASA — very high-frequency sound & ultrasound (paywalled; abstract+DOI)

**URL pulled:** https://pubs.aip.org/asa/jasa/article-abstract/144/4/2511/598839/Effects-of-very-high-frequency-sound-and  

| Field | Value |
|-------|--------|
| Title | Effects of very high-frequency sound and ultrasound on humans. Part I: Adverse symptoms after exposure to audible very-high frequency sound |
| Authors | Fletcher MD, Lloyd Jones S, White PR, Dolder CN, Leighton TG, Lineton B |
| Venue | *J. Acoust. Soc. Am.* 144(4):2511–2520 (2018) |
| DOI | [10.1121/1.5063819](https://doi.org/10.1121/1.5063819) |
| PMID | [30404512](https://pubmed.ncbi.nlm.nih.gov/30404512/) |
| Access | Abstract available; full text paywalled in scrape |

**Abstract (PubMed / publisher abstract page):** Various adverse symptoms from VHFS and US have been reported. Participants were exposed to VHFS/US (13.5–20 kHz, 82–92 dB SPL) and a 1 kHz reference, both ~25 dB above individual threshold, in repeated 3 min blocks with attention task, symptom ratings, and GSR. Participants were pre-grouped symptomatic vs asymptomatic by prior self-attributed VHFS/US history. **In both groups, overall discomfort ratings were higher in the VHFS/US condition than the reference condition.**

**Companion Part II (same JASA issue; not the mandated URL but required context):**

| Field | Value |
|-------|--------|
| Title | … Part II: A double-blind randomized provocation study of inaudible 20-kHz ultrasound |
| DOI | [10.1121/1.5063818](https://doi.org/10.1121/1.5063818) |
| PMID | [30404504](https://pubmed.ncbi.nlm.nih.gov/30404504/) |
| Finding (abstract) | Continuous 20 kHz tone ≥15 dB below detection (~84 dB SPL typical), 20 min, double-blind vs sham: **no evidence US provoked symptoms**; small **nocebo** effects observed |

Also related: public exposure survey DOI [10.1121/1.5063817](https://doi.org/10.1121/1.5063817) (PMID 30404460); 2024 unpleasantness DOI [10.1121/10.0028380](https://doi.org/10.1121/10.0028380) (PMID 39240123).

Raw: `reference/research/raw/jasa-scrape.md`, `fc-vhf-ultrasound.json`, `fc-jasa-vhf-named.json`.

### 2. ScienceDirect PII `S0304394001017591` (paywalled; abstract+DOI)

**URL pulled:** https://www.sciencedirect.com/science/article/pii/S0304394001017591  

| Field | Value |
|-------|--------|
| Title | Hippocampus in relation to mental sweating response evoked by memory recall and mental calculation: a human electroencephalography study with dipole tracing |
| Authors | Homma S, Matsunami K, Han XY, Deguchi K |
| Venue | *Neuroscience Letters* 305(1):1–4 (2001-06-01) |
| DOI | [10.1016/S0304-3940(01)01759-1](https://doi.org/10.1016/S0304-3940(01)01759-1) |
| PMID | [11356293](https://pubmed.ncbi.nlm.nih.gov/11356293/) |
| Access | Abstract + preview; full text paywalled |

**Abstract:** Mental-sweating response (MSR) in the palm during memory recall / mental calculation; MSR-related EEG wavelets ~4 s before MSR; SSB/dipole tracing places one current dipole consistently in the **hippocampus**, the other dispersed in cortex.

**Honest scope note:** This PII resolves to a **hippocampus / MSR / EEG** short communication — **not** airborne ultrasound, pulsed ultrasonics, or infrasound. Cited here because it was a **mandatory URL pull**; do not treat it as ultrasonic-effects evidence. For ultrasound→pain / tactile / somatosensory, use the pulsed-US section below instead.

Raw: `reference/research/raw/pain-scrape.md` (filename legacy; content is Homma 2001).

---

## Infrasound & bodily perception (&lt;20 Hz)

Infrasound ≈ **&lt;20 Hz**: often **felt / structure-coupled** more than heard as pitch. Consumer phone Safari + BT mic/speaker **cannot** faithfully sense or reproduce true infrasound (hardware/HPF). Practical web proxy: **low-frequency linear accelerometer energy** (DeviceMotion), especially chair-coupled nodes.

### PubMed (recent / seminal)

| Year | PMID | DOI | Title |
|------|------|-----|-------|
| 2025 | [41956921](https://pubmed.ncbi.nlm.nih.gov/41956921/) | (see PubMed) | Should limit values be set for infrasound caused by wind turbines? |
| 2023 | [38104341](https://pubmed.ncbi.nlm.nih.gov/38104341/) | [10.13075/mp.5893.01390](https://doi.org/10.13075/mp.5893.01390) | Impact of infrasound and LFN… Part II: epidemiological studies |
| 2023 | [37966387](https://pubmed.ncbi.nlm.nih.gov/37966387/) | [10.13075/mp.5893.01354](https://doi.org/10.13075/mp.5893.01354) | … Part I: experimental studies |
| 2021 | [33940893](https://pubmed.ncbi.nlm.nih.gov/33940893/) | [10.1121/10.0003509](https://doi.org/10.1121/10.0003509) | Annoyance, perception, and physiological effects of wind turbine infrasound |
| (seminal) | PMC [PMC7034801](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7034801/) | — | Activation in human auditory cortex… LFS and infrasound |

Reviews discuss annoyance, sleep, CV markers — evidence mixed/contested; cite primaries, avoid alarmism.

### arXiv

Thin recent set tightly on *human* infrasound perception. Examples: [2303.15603](https://arxiv.org/abs/2303.15603), [1805.01297](https://arxiv.org/abs/1805.01297). **Gap:** 2024–2026 arXiv sparse; PubMed/clinical reviews dominate.

### Firecrawl research index

Hits aligned with Med Pr Parts I–II, wind-turbine annoyance (PMID 33940893), auditory-cortex LFS/IS. See `fc-infrasound.json`, `fc-infrasound-felt.json`.

---

## VHF sound / airborne ultrasound — human effects

Beyond the mandated Fletcher et al. Parts I–II:

| ID | Title / note |
|----|----------------|
| PMID [39240123](https://pubmed.ncbi.nlm.nih.gov/39240123/) · DOI [10.1121/10.0028380](https://doi.org/10.1121/10.0028380) | Sensory unpleasantness of VHFS and audible US (2024) |
| PMID [30404460](https://pubmed.ncbi.nlm.nih.gov/30404460/) | Public exposure to US and VHFS in air |
| PMID [23759188](https://pubmed.ncbi.nlm.nih.gov/23759188/) | Ultrasonic noise — bibliographic review |
| PMID [30657739](https://pubmed.ncbi.nlm.nih.gov/30657739/) | Does airborne ultrasound activate auditory cortex? |
| PMID [30404517](https://pubmed.ncbi.nlm.nih.gov/30404517/) | Short-term exposure to ultrasonic rodent repellent |

Relevance to IoT-ASP hop band (~17–23 kHz): treat **VHFS/US symptom literature** as exposure-ethics context for continuous near-ultrasonic TX; Part II argues **inaudible 20 kHz alone did not reproduce self-reported symptom clusters** under double-blind conditions (nocebo mattered).

---

## Ultrasonic / pulsed / near-ultrasonic

### Near-ultrasonic communication (commodity speakers/mics)

| ID | Title |
|----|-------|
| [arxiv:2103.11261](https://arxiv.org/abs/2103.11261) | High Data Rate Near-Ultrasonic Communication with Consumer Devices |
| [arxiv:2008.00136](https://arxiv.org/abs/2008.00136) | BatNet: Data transmission between smartphones over ultrasound |
| [arxiv:1803.03422](https://arxiv.org/abs/1803.03422) | MOSQUITO: Covert ultrasonic speaker-to-speaker |
| [arxiv:2208.09764](https://arxiv.org/abs/2208.09764) | GAIROSCOPE — ultrasonic → MEMS gyro (mechanical, not audible) |
| [arxiv:2602.02249](https://arxiv.org/abs/2602.02249) | Evaluating Acoustic Data Transmission Schemes… (2026) |

### Pulsed / focused ultrasound — somatosensory / pain (human)

| ID | Title |
|----|-------|
| [PMC3514181](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3514181/) | Pulsed ultrasound differentially stimulates somatosensory circuits (EEG/fMRI) |
| PMID [40039151](https://pubmed.ncbi.nlm.nih.gov/40039151/) | Modulation of ultrasonic stimulation parameters → fine tactile sensations |
| PMID [40030246](https://pubmed.ncbi.nlm.nih.gov/40030246/) | LIFUS on fingertip — fine tactile + hemodynamic responses |
| PMID [12037632](https://pubmed.ncbi.nlm.nih.gov/12037632/) | Temporal summation of pain from nociceptive ultrasonic stimulation |
| PMID [7759656](https://pubmed.ncbi.nlm.nih.gov/7759656/) | Tactile perception of ultrasound (radiation force thresholds) |

**Scope:** These are **contact / focused / mid-air haptic** ultrasonics (kHz–MHz class), not the same as low-level airborne hop tones. Useful for “ultrasound can be felt / nociceptive under specific exposure,” not for equating hop TX to medical US.

Raw: `fc-pulsed-ultrasonic.json`, `search-near-ultrasonic-bt.json`, `search-ultrasonic-vib.json`.

---

## Structure-borne vibration / seats / buildings

| Year | PMID / PMC | Title |
|------|------------|-------|
| 2026 | [42431079](https://pubmed.ncbi.nlm.nih.gov/42431079/) | Accelerometer orientation and sex — seated WBV transmissibility |
| 2026 | [41830678](https://pubmed.ncbi.nlm.nih.gov/41830678/) | Seat suspensions — motion sickness / vibration comfort |
| 2025 | [39874505](https://pubmed.ncbi.nlm.nih.gov/39874505/) | Compliant seat coupled with human body / manikin under WBV |
| 2019 | [PMC10948762](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10948762/) | Vibration reduction — sitting posture / backrest |
| 2016 | [27780424](https://pubmed.ncbi.nlm.nih.gov/27780424/) | Characterisation of human–seat coupling |

Supports **chair-taped accel node**: seat/backrest coupling dominates free handheld; prefer **physical/LF accel** channel for structure-borne vib.

---

## ClinicalTrials.gov

Query `infrasound`: **12 studies** total.

**Exposure / perception-relevant:**

| NCT | Status | Title |
|-----|--------|-------|
| [NCT03459183](https://clinicaltrials.gov/study/NCT03459183) | COMPLETED | Effects of Infra- and Ultrasound on the Brain |
| [NCT03132961](https://clinicaltrials.gov/study/NCT03132961) | TERMINATED | Effects of Infrasound Exposure on Measures of Endolymphatic Hydrops |

Most other hits are medical **infrasound-to-ultrasound e-stethoscopes / hemodynography / vibroacoustic lung** devices — wrong class for environmental exposure claims.

**Honest summary:** sparse registered environmental infrasound exposure trials; do not overclaim a clinical evidence base for the fleet.

---

## Design implication (literature → tooling)

| Class | Literature support | Web implementation honesty |
|-------|--------------------|----------------------------|
| Near-ultrasonic TX 17–23 kHz | NUSC / BatNet / acoustic data TX; VHFS ethics (Fletcher I/II) | Speakers+BT; expect roll-off (`SPEC.md`) |
| Audible / external acoustic | General acoustics | Mic spectrum OK |
| Structure-borne / chair | Seated WBV / human–seat PMIDs | Accel on taped phone |
| Infrasound &lt;20 Hz felt | Perception/annoyance reviews; few CT trials | **LF accel proxy only**; no true infrasound mic/playback claim |
| Pulsed US “felt / pain” | Contact/focused US somatosensory papers | Not equivalent to airborne hop tones |

See also `docs/algorithms.md` (`infra_felt` mode), `docs/gemini-enterprise.md` (5-seat analysis pipeline), `docs/awesome-iot-asp.md` (index).


---

## Navier–Stokes / aeroacoustics / seismo-acoustic coupling

**Pull date:** 2026-09-07. Priors for [docs/physics.md](../docs/physics.md) and ADK autoroute — not on-phone CFD.

### arXiv (relevance-ranked API pull)

| arXiv | Title |
|-------|-------|
| [2307.01775](https://arxiv.org/abs/2307.01775) | Equation for Aeroacoustics in a Quiescent Environment |
| [2401.11300](https://arxiv.org/abs/2401.11300) | Aeroacoustics — Theory and methods… |
| [2509.17986](https://arxiv.org/abs/2509.17986) | Whistling of turbulent cavity flows… linearized compressible Navier–Stokes |
| [2212.12365](https://arxiv.org/abs/2212.12365) | LES of Supersonic Jet Flows for Aeroacoustic Applications |
| [2211.03647](https://arxiv.org/abs/2211.03647) | Numerical simulations of seismo-acoustic nuisance patterns… induced M1.8 |
| [1106.3841](https://arxiv.org/abs/1106.3841) | Giant strain-sensitivity of acoustic energy dissipation… cracks |

Raw: `reference/research/raw/arxiv-navier-stokes-acoustic.xml`, `arxiv-seismo-acoustic.xml`.

### PubMed (seismoacoustic / hydroacoustic)

| PMID | Title (esummary) |
|------|------------------|
| [42561072](https://pubmed.ncbi.nlm.nih.gov/42561072/) | Turbulent seismoacoustic imprints during a hurricane landfall |
| [42246882](https://pubmed.ncbi.nlm.nih.gov/42246882/) | Geophysical and anthropogenic hydroacoustic noise (Alaskan arctic) |
| [42131625](https://pubmed.ncbi.nlm.nih.gov/42131625/) | Tsunami early-warning with DAS — seafloor strains |
| [41810094](https://pubmed.ncbi.nlm.nih.gov/41810094/) | Zoo elephant rumble — combined seismic and acoustic |

**Note:** Several PubMed hits for “Navier-Stokes + ultrasound” were clinical acoustofluidics (e.g. PMID 42689613) — peripheral to building seismo-acoustics; prefer arXiv aeroacoustics + seismo-acoustic PMIDs above for autoroute priors.
