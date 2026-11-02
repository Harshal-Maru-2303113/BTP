# LoRaWAN Domain Knowledge

## What is LoRaWAN?

LoRaWAN (Long Range Wide Area Network) is a wireless protocol for IoT devices. It uses a star-of-stars topology where many end-devices communicate with a central gateway.

### Key Physical Layer Concepts

#### Spreading Factor (SF)
- LoRa uses chirp spread spectrum with 6 spreading factors: SF7 to SF12
- Higher SF = longer range but slower data rate
- SF7: 42 ms for 10 bytes (raw 41.2 ms, fastest)
- SF12: 992 ms for 10 bytes (raw 991.2 ms, slowest, ~24× slower)
- Different SFs are quasi-orthogonal (can transmit simultaneously)

#### Channels
- EU868 band: typically 8 orthogonal carrier frequencies
- Each channel can carry one transmission at a time per SF

#### Time-on-Air (ToA)
The physical transmission duration, determined by:
- Payload size (bytes)
- Spreading factor
- Bandwidth (125 kHz standard)
- Coding rate, preamble, CRC, header mode

Formula from Semtech SX1276 datasheet (AN1200.13, §4.1):
```
T_sym = 2^SF / BW (seconds)
T_preamble = (N_preamble + 4.25) × T_sym
N_payload = 8 + max(ceil((8L - 4·SF + 28 + CRC - 20·IH) / (4·(SF - 2·DE))) × (CR+4), 0)
ToA = (T_preamble + N_payload × T_sym) × 1000 ms
```

#### LoRaWAN Class A Energy Consumption Model (Casals et al. 2017)
Energy across all operational transceiver and microcontroller states:
```
E_cycle = V · ∑ (I_state · t_state)
        = V · (I_mcu·t_mcu + I_sens·t_sens + I_tx·ToA + I_stby·t_wait1 + I_rx·t_rx1 + I_stby·t_wait2 + I_rx·t_rx2 + I_sleep·t_sleep)
```
- Transmit state dominates: $E_{\text{tx}} = V \cdot I_{\text{tx}} \cdot \text{ToA}$.
- For 10 B application payload ($PL = 23\text{ B}$ with 13-byte LoRaWAN MAC overhead):
  - **SF7**: ToA = 61.696 ms, $E_{\text{cycle}} \approx 27.4\text{ mJ}$.
  - **SF12**: ToA = 1482.752 ms, $E_{\text{cycle}} \approx 233.7\text{ mJ}$ ($\approx 8.5\times$ higher!).
- Therefore, **energy minimization directly requires packing packets onto the lowest feasible Spreading Factor (SF7)**.

### Gateway Hardware Constraints

#### Demodulation Limit
- Semtech SX1301/SX1302/SX1303 chips: max **8 concurrent demodulation paths**
- Even though 48 logical channels exist (8 freq × 6 SF), only 8 can simultaneously receive
- Exceeding this causes buffer overflow and packet drops

#### Non-Preemption
- Once a transmission starts on a (SF, Channel) pair, it cannot be interrupted
- No two packets can overlap on the same (SF, Channel)

### Traffic Model

#### Harmonic Periodic Traffic
- Each end-device transmits at a fixed period (e.g., every 10s, 20s, 50s, 100s)
- Periods must divide the hypercycle H to avoid boundary issues
- Within one hypercycle H = 100s, a device with period 10s generates 10 packet instances

#### Real-Time Deadlines
- Each packet has a deadline: D = release + slack_factor × min_feasible_ToA
- Packets that miss deadlines are dropped
- Deadlines are clamped to H

---

## How This Maps to the Scheduling Problem

| LoRaWAN Concept | Scheduling Concept |
|---|---|
| Packet | Job |
| (SF, Channel) pair | Machine |
| Time-on-Air | Processing time p_ij |
| Packet deadline | Job deadline D_i |
| Packet release time | Job release time r_i |
| 8-demod limit | Global resource constraint Ω(t) ≤ 8 |
| "Unrelated" machines | ToA varies drastically by SF (42 ms to 2302 ms integer ceil) |

This is the **R || C_max** problem (scheduling on unrelated parallel machines), which is NP-hard. The 2-approximation is the best known polynomial-time guarantee.

---

## Why Packets Get Dropped (56.8% Drop Rate Explained)

The 133/234 drop rate is due to **physical hardware limitations**, not algorithm weakness:

1. **Synchronous release bottleneck at t=0**: All 50 devices release simultaneously with tight deadlines (~63 ms). Only 8 channels × SF7 can serve them, so at most 8 fit.

2. **SF deadline infeasibility**: With 63 ms deadlines, only SF7 (42 ms for 10 B) is fast enough. SF8 (73 ms) and above exceed the deadline. So all traffic competes for just 8 machines (8 channels × SF7).

3. **No algorithm can schedule more**: Even an optimal algorithm cannot overcome the 8-demod limit and physical ToA constraints.

