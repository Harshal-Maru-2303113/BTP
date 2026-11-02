# Comprehensive Survey: Simulation Parameters & Packet Generation Models in LoRaWAN Research

This document compiles the **exact simulation parameters**, **packet generation models**, and **experimental methodology sections** from the foundational and peer-reviewed research papers in the field of LoRa/LoRaWAN transmission scheduling and performance evaluation.

All corresponding full papers (PDFs, full-text NLM XML, and complete Markdown conversions) are stored locally in the [`papers/`](file:///home/harshal/Projects/BTP/papers) directory.

---

## 1. Summary of Stored Full Papers

| Index | Paper Title & Authors | Venue / Identifier | Local File Path | Key Section |
| :---: | :--- | :--- | :--- | :--- |
| **P1** | **FREE: Fine-Grained Scheduling for Reliable and Energy Efficient Data Collection in LoRaWAN**<br>*K. Qorany, M. Abdellatif, et al.* | IEEE Internet of Things Journal<br>(arXiv:1812.05744) | [`FREE_scheduling_LoRaWAN_arXiv1812.05744.pdf`](file:///home/harshal/Projects/BTP/papers/FREE_scheduling_LoRaWAN_arXiv1812.05744.pdf) | **Section IV & Table V:** Simulation Parameters |
| **P2** | **Modeling the Energy Performance of LoRaWAN**<br>*L. Casals, B. Mir, R. Vidal, C. Gomez* | MDPI *Sensors* 2017<br>(PMC5677147 / DOI: 10.3390/s17102364) | [`casals2017_modeling_energy_lorawan.md`](file:///home/harshal/Projects/BTP/papers/casals2017_modeling_energy_lorawan.md)<br>[`casals2017_modeling_energy_lorawan.xml`](file:///home/harshal/Projects/BTP/papers/casals2017_modeling_energy_lorawan.xml) | **Section 4 & 5, Tables 4–8:** Current States & Evaluation |
| **P3** | **Energy Consumption Model for Sensor Nodes Based on LoRa and LoRaWAN**<br>*T. Bouguera, J.-F. Diouris, et al.* | MDPI *Sensors* 2018<br>(PMC6068831 / DOI: 10.3390/s18072104) | [`bouguera2018_energy_model_sensor_nodes.md`](file:///home/harshal/Projects/BTP/papers/bouguera2018_energy_model_sensor_nodes.md)<br>[`bouguera2018_energy_model_sensor_nodes.xml`](file:///home/harshal/Projects/BTP/papers/bouguera2018_energy_model_sensor_nodes.xml) | **Section 4 & 6, Table 5:** Energy Model & Scenarios |
| **P4** | **Scalability Analysis of Large-Scale LoRaWAN Networks in ns-3**<br>*F. Van den Abeele, J. Haxhibeqiri, et al.* | IEEE Internet of Things Journal<br>(arXiv:1705.05899) | [`Scalability_ns3_LoRaWAN_arXiv1705.05899.pdf`](file:///home/harshal/Projects/BTP/papers/Scalability_ns3_LoRaWAN_arXiv1705.05899.pdf) | **Section V-A & Fig. 7:** Upstream Traffic & ns-3 Setup |
| **P5** | **Understanding the Limits of LoRaWAN**<br>*F. Adelantado, X. Vilajosana, et al.* | IEEE Communications Magazine 2017<br>(arXiv:1607.08011) | [`adelantado2017_understanding_limits_lorawan.pdf`](file:///home/harshal/Projects/BTP/papers/adelantado2017_understanding_limits_lorawan.pdf) | **Section "LoRaWAN Overview" & "Limits":** Duty-Cycle & Load |
| **P6** | **Fair Adaptive Data Rate Allocation and Power Control in LoRaWAN**<br>*F. Cuomo, M. Campo, et al.* | IEEE INFOCOM / IoT Workshops<br>(arXiv:1802.10338) | [`Fair_ADR_Power_Control_LoRaWAN_arXiv1802.10338.pdf`](file:///home/harshal/Projects/BTP/papers/Fair_ADR_Power_Control_LoRaWAN_arXiv1802.10338.pdf) | **Section IV-B & Table II:** Simulation Parameters |
| **P7** | **A Thorough Study of LoRaWAN Performance Under Different Parameter Settings**<br>*G. A. Abed, M. Capuzzo, et al.* | Wireless Communications & Mobile Computing<br>(arXiv:1906.05083) | [`Thorough_Study_LoRaWAN_Parameters_arXiv1906.05083.pdf`](file:///home/harshal/Projects/BTP/papers/Thorough_Study_LoRaWAN_Parameters_arXiv1906.05083.pdf) | **Section IV & Tables I–III:** Setup, Interarrivals & GW Chains |
| **P8** | **Mathematical Model of LoRaWAN Channel Access**<br>*D. Bankov, E. Khorov, A. Lyakhov* | IEEE WoWMoM / Access<br>(arXiv:2004.07645) | [`Mathematical_Model_LoRaWAN_Bankov_arXiv2004.07645.pdf`](file:///home/harshal/Projects/BTP/papers/Mathematical_Model_LoRaWAN_Bankov_arXiv2004.07645.pdf) | **Section IV & V:** Poisson Traffic & EU868 DR Distribution |
| **P9** | **Mathematical Model of LoRaWAN Channel Access with Capture Effect**<br>*D. Bankov, E. Khorov, A. Lyakhov* | IEEE PIMRC<br>(arXiv:2008.03140) | [`LoRaWAN_Capture_Effect_Bankov_arXiv2008.03140.pdf`](file:///home/harshal/Projects/BTP/papers/LoRaWAN_Capture_Effect_Bankov_arXiv2008.03140.pdf) | **Section III & IV:** Capture Matrix & Retransmission Load |
| **P10** | **A Model for Reliable Uplink Transmissions in LoRaWAN**<br>*M. Capuzzo, D. Magrin, A. Zanella* | IEEE Transactions on Cognitive Comm.<br>(arXiv:2009.09397) | [`Model_Reliable_Uplink_LoRaWAN_arXiv2009.09397.pdf`](file:///home/harshal/Projects/BTP/papers/Model_Reliable_Uplink_LoRaWAN_arXiv2009.09397.pdf) | **Section V & Table II:** Default Parameters & Retransmissions |
| **P11** | **Slotted ALOHA on LoRaWAN - Design, Analysis, and Deployment**<br>*T. Polonelli, D. Brunelli, et al.* | MDPI *Sensors* 2019<br>(arXiv:1902.09468) | [`Slotted_ALOHA_LoRaWAN_arXiv1902.09468.pdf`](file:///home/harshal/Projects/BTP/papers/Slotted_ALOHA_LoRaWAN_arXiv1902.09468.pdf) | **Section 3 & 4:** Slot Duration, Airtime Overhead & Collision |
| **P12** | **Semtech SX1276/77/78/79 Transceiver Datasheet**<br>*Semtech Corporation* | Official Product Specification | [`semtech_sx1276_rfm95_datasheet.pdf`](file:///home/harshal/Projects/BTP/papers/semtech_sx1276_rfm95_datasheet.pdf) | **Section 4.1.1.7:** Time-on-Air (ToA) Formulas & Framing |

---

## 2. In-Depth Extraction of Simulation Parameters & Traffic Models

### Paper 1: Qorany et al. (IEEE IoT-J) — Fine-Grained Transmission Scheduling
- **Section Reference:** *Section IV: Performance Evaluation*, Subsection *A. Packet Lengths* and *Table V*.
- **Traffic & Packet Generation:**
  - **Distribution:** Poisson process for raw generation; aggregated into periodic bulk transmission (`goal buffer`).
  - **Payload Size ($L$):** $20\text{ bytes}$ base telemetry data.
  - **Packet Periodicity ($T$):** Periodic collection intervals ranging from $1\text{ hour}$ to $48\text{ hours}$; internal packet arrival rate $\sim 20\text{ B}$ every exponential $5\text{ minutes}$.
  - **Initial Offsets:** Uniform random desynchronization offset $U(0, 600\text{ s})$ to mitigate systematic collisions at $t=0$.
- **Network & Hardware Parameters:**
  - **Devices ($N$):** $10$ to $2,000$ nodes randomly scattered.
  - **Gateway Channels:** 3 default $+ 5$ additional $= 8$ channels.
  - **Concurrent Receptions ($N_{\text{demod}}^{\max}$):** Exactly **8 concurrent paths** at the gateway.
  - **Bandwidth & Spreading Factor:** $BW = 125/500\text{ kHz}$, $SF \in \{7, 8, 9, 10, 11, 12\}$, $CR = 4/5$.
  - **MAC Headers:** $7\text{ bytes}$ standard LoRaWAN header $+ 1\text{ byte}$ ordering header.

---

### Paper 2: Casals et al. (MDPI Sensors 2017) — LoRaWAN Energy Performance Modeling
- **Section Reference:** *Section 4: Modeling LoRaWAN End-Device Current Consumption* and *Section 5: Evaluation*.
- **Traffic & Packet Generation:**
  - **Traffic Type:** Periodic unacknowledged and acknowledged uplink transmission from Class A end-devices.
  - **Payload Size ($L$):** Variable evaluations across $L \in \{1, 10, 20, 50, 100\}\text{ bytes}$.
  - **Transmission Period ($T_{\text{interval}}$):** Range from $T = 5\text{ minutes}$ to $T = 24\text{ hours}$.
- **Electrical & Physical Parameters (from Table 4–7):**
  - **Supply Voltage ($V$):** $3.3\text{ V}$.
  - **Sleep Current ($I_{\text{sleep}}$):** $45\text{ }\mu\text{A}$ ($0.045\text{ mA}$) (active RTC / low-power sleep).
  - **Transmit Current ($I_{\text{tx}}$):** $38.0\text{ mA}$ at $+14\text{ dBm}$ output power ($125\text{ kHz}$).
  - **Receive Windows ($I_{\text{rx1}}, I_{\text{rx2}}$):** $38.0\text{ mA}$ (active demodulation during window).
  - **Standby & Radio Preparation ($I_{\text{prep}}, I_{\text{post}}$):** $13.4\text{ mA}$ to $20.9\text{ mA}$ for $T_{\text{prep}} = 10.4\text{ ms}$, $T_{\text{post}} = 272.5\text{ ms}$.

---

### Paper 3: Bouguera et al. (MDPI Sensors 2018) — Sensor Node Energy Model
- **Section Reference:** *Section 6: Numerical Results and Discussions* and *Table 5*.
- **Traffic & Packet Generation:**
  - **Traffic Type:** Periodic environmental acceleration and temperature monitoring.
  - **Payload Size ($L$):** $10\text{ to } 51\text{ bytes}$ application payload.
  - **Measurement Periods ($T_{\text{meas}}$):** $30\text{ s}, 60\text{ s}, 300\text{ s}, 3600\text{ s}$.
- **Hardware Profile:**
  - Battery capacity: $950\text{ mAh}$ at $3.3\text{ V}$.
  - Processing energy: STM32L4 MCU running at $80\text{ MHz}$, $T_{\text{proc}} = 5\text{ ms}$, $I_{\text{proc}} = 10\text{ mA}$.
  - Radio states: SX1276 transceiver operating at $868\text{ MHz}$ under $SF7$ through $SF12$.

---

### Paper 4: Van den Abeele et al. (ns-3 Scalability Study)
- **Section Reference:** *Section V-A: Simulation Scenarios and Traffic Profiles*.
- **Traffic & Packet Generation:**
  - **Uplink Data Periods:** $T \in \{600\text{ s}, 6{,}000\text{ s}, 60{,}000\text{ s}\}$.
  - **Packet Timing:** Initial packet transmission time is drawn uniformly at random: $t_0 \sim U(0, T)$. Subsequent packets follow strictly periodic intervals of length $T$.
  - **Payload Sizes:** Application payload $= 8\text{ bytes}$, producing a total physical payload of $21\text{ bytes}$ (due to $13\text{ bytes}$ of MAC header, FHDR, and MIC).
  - **Downlink Generation:** Poisson / Exponential inter-arrival with mean $60{,}000\text{ s}$ ($1$ downlink per $10$ or $100$ uplinks).
- **Network Deployment:**
  - Cell radius: $6{,}100\text{ m}$.
  - Path loss: Log-distance path loss with exponent $\gamma = 2.08$, reference loss $46.68\text{ dB}$ at $1\text{ m}$.

---

### Paper 5: Cuomo et al. (Fair ADR & Power Control)
- **Section Reference:** *Section IV-B: Simulation Parameters*, *Table II*.
- **Simulation Setup:**
  - **Nodes ($N$):** $100$ to $4{,}000$ end-devices.
  - **Packet Length ($L$):** $80\text{ bytes}$.
  - **Transmission Period ($1/\lambda$):** $60\text{ seconds}$.
  - **Max Concurrent Reception:** Exactly $8$ (gateway hardware channels).
  - **Simulation Duration:** $86{,}400\text{ seconds}$ ($24\text{ hours}$).
  - **Frequency:** $868\text{ MHz}$.

---

### Paper 6: Abed et al. (A Thorough Study of LoRaWAN Parameters)
- **Section Reference:** *Section IV: Simulation Setup and Scenarios*, Subsections *A–B*, *Tables I–III*.
- **Simulation Parameters:**
  - **Gateway Architecture:** SX1301 digital baseband processor featuring **8 parallel multi-SF demodulation paths** capable of simultaneous decoding on arbitrary carrier frequencies.
  - **Channel Plan:** European EU868 standard ($868.1, 868.3, 868.5\text{ MHz}$ plus expansion frequencies, $BW = 125\text{ kHz}$).
  - **Duty Cycle:** $1\%\text{ mandatory}$ on EU868 uplink sub-band; $10\%$ on dedicated downlink channel ($869.525\text{ MHz}$).
  - **Retransmission Limits:** Max attempts $m \in \{1, 2, 4, 6, 8\}$.
  - **Inter-arrival Rates:** Tested across $\lambda \in [10^{-2}, 10^0]\text{ packets/s}$ ($T \in [1\text{ s}, 100\text{ s}]$).

---

### Paper 7: Bankov et al. (Mathematical Models of Channel Access)
- **Section Reference:** *Section IV & V: Numerical Results*.
- **Traffic Model:**
  - Total network packet arrival follows a Poisson process with aggregate rate $\Lambda = \sum \lambda_i$.
  - Data rates distributed across EU868 according to path loss:
    $$p_0 (SF12) = 0.28,\quad p_1 (SF11) = 0.20,\quad p_2 (SF10) = 0.14,\quad p_3 (SF9) = 0.10,\quad p_4 (SF8) = 0.08,\quad p_5 (SF7) = 0.20$$
  - Demonstrates that when network load exceeds $0.1\text{ packets/s}$, uncoordinated ALOHA causes severe collision avalanche, proving the necessity of coordinated/scheduled access.

---

### Paper 8: Semtech SX1276 Official Datasheet
- **Section Reference:** *Section 4.1.1.7: Time on Air*.
- **Formulas:**
  - Symbol duration:
    $$T_s = \frac{2^{SF}}{BW}$$
  - Preamble duration:
    $$T_{\text{preamble}} = (N_{\text{preamble}} + 4.25) \cdot T_s$$
  - Payload symbol count:
    $$N_{\text{payload}} = 8 + \max\left( \left\lceil \frac{8L - 4SF + 28 + 16 - 20H}{4(SF - 2DE)} \right\rceil (CR + 4), \; 0 \right)$$
  - Total Time-on-Air (ToA):
    $$T_{\text{packet}} = T_{\text{preamble}} + N_{\text{payload}} \cdot T_s$$

---

## 3. Direct Alignment with This Project's Benchmark Configuration

In our project ([`config.json`](file:///home/harshal/Projects/BTP/config.json) and [`main.tex`](file:///home/harshal/Projects/BTP/main.tex) Section VII-A), our simulation parameters and packet generator were intentionally designed to match this peer-reviewed consensus:

| Parameter | Literature Consensus | Our Benchmark Setting (`config.json` / `main.tex`) | Rationale & Citation |
| :--- | :--- | :--- | :--- |
| **Gateway Demodulators** | 8 concurrent paths (SX1301/SX1302) | $N_{\text{demod}}^{\max} = 8$ concurrent paths | Qorany et al. (Table V); Abed et al. (§IV-A); Cuomo et al. (Table II) |
| **Carrier Channels** | 8 frequencies in EU868 ($868.1 - 869.5\text{ MHz}$) | $N_{\text{ch}} = 8$ channels | EU868 ETSI standard; Bankov et al. (2020) |
| **Spreading Factors** | $SF \in \{7, 8, 9, 10, 11, 12\}$ | $SF \in \{7, 8, 9, 10, 11, 12\}$ ($6$ levels) | Semtech SX1276 (§4.1.1.7); Casals et al. (Table 6) |
| **Virtual Machines** | $m = N_{\text{ch}} \times N_{\text{sf}} = 48$ | $m = 8 \times 6 = 48$ unrelated machines | Gairing et al. (2007); Lenstra et al. (1990) |
| **Payload Sizes ($L$)** | $8\text{ to } 80\text{ bytes}$ | $L \in \{10, 20, 30, 50\}\text{ bytes}$ | Van den Abeele (8B); Qorany (20B); Cuomo (80B) |
| **Traffic Periodicity ($T$)** | Periodic telemetry ($10\text{ s}$ to $100\text{ s}$) | Harmonic periods $T \in \{10, 20, 50, 100\}\text{ s}$ | Van den Abeele (§V-A); Casals (§4) |
| **Hypercycle Duration** | System LCM of harmonic streams | $H = \text{LCM}(10, 20, 50, 100) = 100\text{ s}$ | Real-time cyclic executive theory (Liu & Layland) |
| **Total Packet Count ($n$)** | Hundreds to thousands per cycle | $n = 234\text{ packets}$ ($50\text{ periodic streams}$) | Sufficient density to test saturation while verifying exact B&B optimum |
| **Radio Energy Model** | Class A state current integration | Casals et al. multi-state current model ($V=3.3\text{V}, I_{\text{tx}}=38\text{mA}, I_{\text{sleep}}=45\mu\text{A}$) | Casals et al. (Sensors 2017); Bouguera et al. (Sensors 2018) |
