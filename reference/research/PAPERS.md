# Research papers (Firecrawl research index)

Canonical synthesis: [`../LITERATURE.md`](../LITERATURE.md) · Index: [`../../docs/awesome-iot-asp.md`](../../docs/awesome-iot-asp.md).

Queries: near-ultrasonic comms, VHFS/US human effects, pulsed ultrasonics, smartphone vibration sensing, human–seat structure-borne vibration, infrasound felt &lt;20 Hz.

## Mandated / named

- **JASA Part I** PMID 30404512 · DOI 10.1121/1.5063819 — VHFS adverse symptoms (abstract+DOI; paywalled). See `raw/jasa-scrape.md`.
- **JASA Part II** PMID 30404504 · DOI 10.1121/1.5063818 — inaudible 20 kHz double-blind.
- **ScienceDirect PII S0304394001017591** PMID 11356293 · DOI 10.1016/S0304-3940(01)01759-1 — Homma et al. hippocampus/MSR (*not* ultrasonics). See `raw/pain-scrape.md`.


## Source file: `search-near-ultrasonic-bt.json`

## [arxiv:2103.11261] High Data Rate Near-Ultrasonic Communication with Consumer Devices
Automating device pairing and credential exchange in consumer devices reduce the time users spend with mundane tasks and improve the user experience. Acoustic communication is gaining traction as a practical alternative to Bluetooth or Wi-Fi because it can enable quick and localized information transfer between consumer devices with built-in hardware. However, achieving high data rates (>1 kbps) in such systems has been a challenge because the systems and methods chosen for communication were not tailored to the application. In this work, a high data rate, near-ultrasonic communication (NUSC) 

## [arxiv:1803.03422] MOSQUITO: Covert Ultrasonic Transmissions between Two Air-Gapped Computers using Speaker-to-Speaker Communication
In this paper we show how two (or more) airgapped computers in the same room, equipped with passive speakers, headphones, or earphones can covertly exchange data via ultrasonic waves. Microphones are not required. Our method is based on the capability of a malware to exploit a specific audio chip feature in order to reverse the connected speakers from output devices into input devices - unobtrusively rendering them microphones. We discuss the attack model and provide technical background and implementation details. We show that although the reversed speakers/headphones/earphones were not origi

## [pmid:30404497] Wireless communication between personal electronic devices and hearing aids using high frequency audio and ultrasound.
Hearing aids continue to be the main intervention for hearing loss but ease of use and control is of concern due to the small size of these aids. While technological advances in Bluetooth Low Energy have allowed for improved wireless control, in particular between personal…

## [arxiv:2008.00136] BatNet: Data transmission between smartphones over ultrasound
In this paper, we present BatNet, a data transmission mechanism using ultrasound signals over the built-in speakers and microphones of smartphones. Using phase shift keying with an 8-point constellation and frequencies between 20--24kHz, it can transmit data at over 600bit/s up to 6m. The target application is a censorship-resistant mesh network. We also evaluated it for Covid contact tracing but concluded that in this application ultrasonic communications do not appear to offer enough advantage over Bluetooth Low Energy to be worth further development.

## [arxiv:2602.02249] Evaluating Acoustic Data Transmission Schemes for Ad-Hoc Communication Between Nearby Smart Devices
Acoustic data transmission offers a compelling alternative to Bluetooth and NFC by leveraging the ubiquitous speakers and microphones in smartphones and IoT devices. However, most research in this field relies on simulations or limited on-device testing, which makes the real-world reliability of proposed schemes difficult to assess. We systematically reviewed 31 acoustic communication studies for commodity devices and found that none provided accessible source code. After contacting authors and re-implementing three promising schemes, we assembled a testbed of eight representative acoustic com

## [pmid:27214897] Full-Duplex Airborne Ultrasonic Data Communication Using a Pilot-Aided QAM-OFDM Modulation Scheme.
Orthogonal frequency division multiplexing (OFDM) has been extensively used in a variety of broadband digital wireless communications applications because of its high bandwidth utilization efficiency and effective immunity to multipath distortion. This paper has investigated…


## Source file: `search-structure-borne.json`

## [pmcid:PMC10948762] Vibration reduction of human body biodynamic response in sitting posture under vibration environment by seat backrest support.
Four-degree-of-freedom (4-DOF) human-chair coupling models are constructed to characterize the different contact modes between the head, chest back, waist back and backrest. The seat-to-head transfer ratio (STHT) is used as an evaluation metric for vibration reduction…

## [pmid:39874505] Dynamic characteristics of a compliant seat coupled with the human body and a manikin during the exposure to the whole-body vibration: effect of the polyurethane foam, the track position and the measurement location.
Transmissibility is used to assess dynamic responses of the occupant-seat system, and most studies have exclusively assessed the transmissibility from the floor to the cushion or the backrest surface with the human body. In this investigation, the vertical vibration transmitted…

## [pmid:27780424] Characterisation of the human-seat coupling in response to vibration.
Characterising the coupling between the occupant and vehicle seat is necessary to understand the transmission of vehicle seat vibration to the human body. Major coupling between the human body and the vehicle seat-structure was observed in the frequency range of 10-60 Hz. There…

## [pmid:25017144] Effects of seat structural dynamics on current ride comfort criteria.
The ISO 2631-1 ( 1997 ) provides methodologies for assessment of the seated human body comfort in response to vibrations. The standard covers various conditions such as frequency content, direction and location of the transmission of the vibration to the human body. However, the…

## [pmid:42431079] Effects of accelerometer orientation and sex on transmissibility during seated whole-body vibration exposure.
Four orthogonal motion capture markers were attached to accelerometers at S1 and T6 to correct acceleration data to the BCS.

## [pmid:19088407] Energy absorption of seated occupants exposed to horizontal vibration and role of back support condition.
Absorbed power characteristics of seated human subjects under fore-aft (x-axis) and lateral (y-axis) vibration are investigated through measurements of dynamic interactions at the two driving-points formed by the body and the seat pan, and upper body and the backrest. The…


## Source file: `search-ultrasonic-vib.json`

## [arxiv:2004.06195] AiR-ViBeR: Exfiltrating Data from Air-Gapped Computers via Covert Surface ViBrAtIoNs
Air-gap covert channels are special types of covert communication channels that enable attackers to exfiltrate data from isolated, network-less computers. Various types of air-gap covert channels have been demonstrated over the years, including electromagnetic, magnetic, acoustic, optical, and thermal. In this paper, we introduce a new type of vibrational (seismic) covert channel. We observe that computers vibrate at a frequency correlated to the rotation speed of their internal fans. These inaudible vibrations affect the entire structure on which the computer is placed. Our method is based on

## [pmid:41118281] Theory and Analysis of High-Sensitivity Acceleration Sensing Based on 2-D Phononic Crystals.
It introduces a novel approach where ultrasound is utilized for the first time to sense acceleration through the PnCs structure. Acceleration causes a frequency shift in these peaks. Both numerical and experimental results demonstrate that this approach is suitable for…

## [arxiv:2007.03874] Fine-grained Vibration Based Sensing Using a Smartphone
Recognizing surfaces based on their vibration signatures is useful as it can enable tagging of different locations without requiring any additional hardware such as Near Field Communication (NFC) tags. However, previous vibration based surface recognition schemes either use custom hardware for creating and sensing vibration, which makes them difficult to adopt, or use inertial (IMU) sensors in commercial off-the-shelf (COTS) smartphones to sense movements produced due to vibrations, which makes them coarse-grained because of the low sampling rates of IMU sensors. The mainstream COTS smartphone

## [pmcid:PMC10892134] Investigation of New Accelerometer Based on Capacitive Micromachined Ultrasonic Transducer (CMUT) with Ring-Perforation Membrane.
Capacitive micromachined ultrasonic transducer (CMUT) has been widely studied due to its excellent resonance characteristics and array integration. This paper presents the first study of the CMUT electrostatic stiffness resonant accelerometer. To improve the sensitivity of the…

## [arxiv:2603.28787] Smartphone-Based Identification of Unknown Liquids via Active Vibration Sensing
Traditional liquid identification instruments are often unavailable to the general public. This paper shows the feasibility of identifying unknown liquids with commercial lightweight devices, such as a smartphone. The key insight is that different liquid molecules have different viscosity coefficients and therefore must overcome different energy barriers during relative motion. With this intuition in mind, we introduce a novel model that measures liquids' viscosity based on active vibration. However, building a robust system using built-in smartphone accelerometers is challenging. Practical is

## [pmcid:PMC6679289] Extraction of Bridge Fundamental Frequencies Utilizing a Smartphone MEMS Accelerometer.
Therefore, it cannot be directly used to track feeble vibrations such as structural vibrations.

## [arxiv:2208.09764] GAIROSCOPE: Injecting Data from Air-Gapped Computers to Nearby Gyroscopes
It is known that malware can leak data from isolated, air-gapped computers to nearby smartphones using ultrasonic waves. However, this covert channel requires access to the smartphone's microphone, which is highly protected in Android OS and iOS, and might be non-accessible, disabled, or blocked. In this paper we present `GAIROSCOPE,' an ultrasonic covert channel that doesn't require a microphone on the receiving side. Our malware generates ultrasonic tones in the resonance frequencies of the MEMS gyroscope. These inaudible frequencies produce tiny mechanical oscillations within the smartphone

## [pmid:28332815] Detecting Subtle Vibrations Using Graphene-Based Cellular Elastomers.
Ultralight graphene elastomer-based flexible sensors are developed to detect subtle vibrations within a broad frequency range. The same device can be employed as an accelerometer, tested within the experimental bandwidth of 20-300 Hz as well as a microphone, monitoring sound…

