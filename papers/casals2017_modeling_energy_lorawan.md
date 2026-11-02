# Modeling the Energy Performance of LoRaWAN

**Authors:** Lluís Casals, Bernat Mir, Rafael Vidal, Carles Gomez

**Journal:** Sensors (Basel, Switzerland) | **DOI:** 10.3390/s17102364 | **PMCID:** PMC5677147

---

## Abstract

LoRaWAN is a flagship Low-Power Wide Area Network (LPWAN) technology that has highly attracted much attention from the community in recent years. Many LoRaWAN end-devices, such as sensors or actuators, are expected not to be powered by the electricity grid; therefore, it is crucial to investigate the energy consumption of LoRaWAN. However, published works have only focused on this topic to a limited extent. In this paper, we present analytical models that allow the characterization of LoRaWAN end-device current consumption, lifetime and energy cost of data delivery. The models, which have been derived based on measurements on a currently prevalent LoRaWAN hardware platform, allow us to quantify the impact of relevant physical and Medium Access Control (MAC) layer LoRaWAN parameters and mechanisms, as well as Bit Error Rate (BER) and collisions, on energy performance. Among others, evaluation results show that an appropriately configured LoRaWAN end-device platform powered by a battery of 2400 mAh can achieve a 1-year lifetime while sending one message every 5 min, and an asymptotic theoretical lifetime of 6 years for infrequent communication.


## 1. Introduction

Low-Power Wide Area Networks (LPWAN) define a category of wireless communication technologies that have recently gained significant momentum. Industry, academia and standards development organizations have devoted significant efforts to LPWAN in the last years [1,2]. Such technologies typically offer a link range of one or more kilometers, while a single infrastructure element (often called a gateway) is capable of supporting hundreds of thousands of devices such as sensors and actuators [3,4]. Therefore, LPWAN technologies enable Internet of Things (IoT) applications, such as smart cities, by means of low cost and low complexity infrastructure.


Among LPWAN technologies, LoRaWAN (and its related modulation, LoRa), is perhaps the technology that has attracted the attention of most academic work as of the writing of this paper [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]. This can be explained by the public availability of its specifications [27], the availability of certified hardware [28] and the fact that LoRaWAN communication can be enabled without the need to establish a relationship with an operator.


Many LoRaWAN devices, such as sensors or actuators, will typically be battery-operated. Therefore, it is crucial to investigate the characteristics of LoRaWAN energy consumption. However, published works only focus on this topic to a limited extent, providing only rough estimates on parameters related with LoRaWAN energy performance, while not considering realistic behavior of LoRaWAN device hardware, as well as the impact of the main LoRaWAN parameters and mechanism settings [13,22,25,26].


In this paper, we present analytical models that characterize device current consumption, device lifetime and energy cost of data delivery with LoRaWAN. For a realistic analysis, the models are derived based on measurements performed on a currently prevalent LoRaWAN platform. The models developed allow studying the impact of relevant LoRaWAN parameters and mechanisms such as data rates, acknowledged transmission and payload size, as well as Bit Error Rate (BER) and collisions, on LoRaWAN energy performance. Evaluation results illustrate energy performance and trade-offs of LoRaWAN. Among others, we have found that using an appropriate configuration a LoRaWAN end-device platform powered by a 2400 mAh battery can achieve a 1-year lifetime while sending one message every 5 min, and an asymptotic theoretical lifetime of 6 years as communication becomes infrequent.


The remainder of the paper is organized as follows. Section 2 reviews related work. Section 3 overviews LoRaWAN, describing its general architecture and focusing on its physical and MAC layers. Section 4 models LoRaWAN end-device current consumption, end-device lifetime, and energy cost of data delivery, whereas Section 5 provides evaluation results obtained by using the models presented. Section 6 concludes the paper.


## 2. Related Work

Most of the research done on LoRa/LoRaWAN has focused on features such as coverage, robustness, capacity, scalability, delay and throughput [3,5,6,7,8,9,10,11,12]. However, a characteristic such as energy consumption, which is crucial considering that many LoRa/LoRaWAN devices will not be grid-powered, has received limited attention. We next review the literature on LoRaWAN energy consumption. We first focus on current consumption details of LoRa/LoRaWAN devices reported in published works, and secondly we discuss the few existing models of LoRa/LoRaWAN energy consumption, node lifetime or energy cost of data delivery.


Several works provide current consumption data of LoRa/LoRaWAN devices, obtained from a datasheet or by empirical means [12,13,14,15,16,17,18,19,20,21,22]. Such details, which are summarized in Table 1, correspond to sleep, transmission and reception device states. As it can be seen, sleep current ranges from 7.66 μA to 34 mA (or between 30.9 μA and 3.4 mA excluding LoRa-only and custom devices). Sleep current for the considered hardware platforms is up to several orders of magnitude greater than that of their transceivers (see Table 2), which can be near or even lower than 1 μA. One important conclusion is that current LoRa/LoRaWAN nodes are far from the degree of optimization exhibited by platforms that use other low power technologies. For example, IEEE 802.15.4 and Bluetooth Low Energy (BLE) commercial devices feature a sleep current near 1 μA [23,24]. Therefore, in order to achieve attractive node lifetime figures (e.g., in the order of years), current LoRaWAN nodes need batteries with greater capacity than typical button cell batteries, e.g., of AA type, which however have bigger size and are more expensive. We attribute the sleep current in LoRaWAN devices to suboptimal hardware integration of device components, e.g., the microcontroller and the transceiver.


Based on the characterization of sleep, transmit and receive states of a LoRa/LoRaWAN device, a few analytical models of LoRa/LoRaWAN energy consumption, node lifetime or energy cost of data delivery have been published [13,22,25,26]. However, these models are too simple, since there exist several other states for a LoRa/LoRaWAN device involved in a communication that need to be considered (see Section 4). Next, we briefly present the main results and other limitations of these works. An accurate calculation of message transmission time is only provided in [25], however the study only focuses on LoRa, and therefore it does not model the MAC layer mechanisms defined in LoRaWAN, such as use of acknowledgments, receive windows, and retransmissions (see Section 3). In [13], which focuses only on optimizing downlink communications, fixed LoRaWAN settings (i.e., a single DR and acknowledged transmission) are considered. Energy consumption of 0.05–0.44 mJ and a battery lifetime between 13 and 1 year, respectively, are obtained for a device running on two AA batteries, when transferring data from 1 to 10 times per hour. However, one of the most important values used in the model, the sleep current (of 2 µA), is without explanation significantly lower than the corresponding value in the datasheet published by the manufacturer (i.e., 30.9 µA). In [26], only the energy related to the activation of a LoRaWAN node by using the On-The-Air Activation (OTAA) mode is modeled. In [22], the battery capacity consumed during a day by a device is calculated assuming 100 events detected and 10 frame transmissions performed by the device. The result is 222.66 µAh, which corresponds to a lifetime of 21.5 months for a 150 mAh button cell battery. Neither the impact of using acknowledgments, nor the influence of the DR configured are considered. Finally, the impact of errors due to corruption on LoRaWAN energy performance has not been modeled in publicly available works.


Based on the literature review, we conclude that, to the best of our knowledge, this paper is the first one that provides a detailed analytical model of node energy consumption, node lifetime and energy cost of data delivery, considering real LoRaWAN device hardware behavior and physical and MAC layer parameters and mechanisms.


## 3. LoRaWAN Overview

In this section, we present fundamental LoRaWAN characteristics. We describe the protocol architecture as well as the physical and MAC layers, highlighting the mechanisms, procedures and key parameters that are relevant in the scope of this paper. This section is organized in three subsections. The first one provides a general LoRaWAN overview, whereas the remaining two subsections focus on physical and link layer functionality.


## 3.1. LoRaWAN General Overview

LoRaWAN is a wireless communication technology designed to achieve long range while consuming low power, based on a one-hop radio system. This approach allows overcoming some important issues related with deployment complexity and low energy routing protocols, among others [18]. On the other hand, LoRaWAN exhibits communication constraints, which may limit the suitability of this technology for present and future IoT applications.


A LoRaWAN network is based on a star-of-stars topology composed of three basic elements: end-devices, gateways and a central network server (see Figure 1a) [27]. End-devices, which may correspond to e.g., sensors or actuators, communicate with the network server through one or more gateways, while the network server sends messages to end-devices through a specific gateway. End-devices use the LoRa physical layer to exchange messages with the gateway, while the gateway and the network server communicate over an IP-based protocol stack (Figure 1b).


LoRAWAN provides end-to-end encryption and data integrity. Upper layer payloads are encrypted by means of an Application Session Key, which provides confidentiality. On the other hand, a Network Session Key is used to provide data integrity over the ciphertext payload and a subset of header fields [27].


LoRaWAN specification defines three functionality classes: Class A, Class B and Class C. Class A must be implemented by all LoRaWAN devices, and is also known as basic LoRaWAN. Class A allows bidirectional communication between an end-device and the network server, which is scheduled by the end-device based on its needs. In this functionality class, downlink transmission (i.e., from the network server to the end-device) can only occur after an uplink transmission (i.e., from the end-device to the network server).


Class B is based on class A; however, it supports additional downlink transmission opportunities at prescheduled times. On the other hand, Class C allows downlink transmission at any time, except when the end-device is transmitting. Class C end-devices consume greater power to operate, but offer the lowest latency, compared with Class A and Class B end-devices. Both Class B and Class C are optional, and are in consequence not typically supported by LoRaWAN devices.


The study presented in this paper focuses on Class A LoRaWAN operation. The next two subsections present physical layer and MAC layer details for this LoRaWAN mode.


## 3.2. LoRaWAN Physical Layer

## 3.2.1. Physical Layer Main Features

LoRa modulation and Gaussian Frequency Shift Keying (GFSK) provide the physical transmission support for communication between the end-device and the gateway. LoRa modulation is based on chirp spread spectrum mechanism [38]. Each LoRa symbol is composed of 2SF chirps, where SF represents the corresponding spreading factor [7]. The use of six orthogonal SFs in the range of 7 to 12, which provide different Data Rates (DRs), results in a better spectral efficiency and an increased network capacity. LoRa modems also use forward error correction, adding a small overhead to the transmitted message, which provides recovery features against bit corruption. This is implemented through different Coding Rates (CRs), from 4/5 to 4/8 (denoted CR = 1 to CR = 4, respectively). On the other hand, to avoid issues regarding drift of the crystal reference oscillator, a low data rate optimization mechanism is applied, which adds a small overhead to increase robustness to frequency variation over the timescale of the LoRa message [38]. This is done for SF = 11 and SF = 12.


The Radio Frequency (RF) band to be used depends on the country where LoRaWAN is deployed. Our study considers operation in the European region, in the EU863–870 Industrial Scientific Medical (ISM) band, where three default channels are defined: 868.10, 868.30, 868.50 MHz. Each one of these channels has a bandwidth of 125 kHz, uses the LoRa modulation, and must allow data rates from 0.3 kbps to 5 kbps (DR0 to DR5, see Table 3). These channels must be implemented in every end-device within the European region. LoRaWAN also enforces duty-cycle limitations stated by ETSI regulations. For the sub-band comprising between 868.0 MHz to 868.6 MHz, the duty-cycle must be <1%. Then, this duty cycle has to be distributed in the three channels of this sub-band [18]. Note, however, that ETSI regulations limit the duty-cycle over one-hour intervals, whereas LoRaWAN enforces compliance with such limitation over the interval between transmission of a message and the next one. The reference indices for each data rate (DR), and the corresponding spreading factor (SF), bandwidth and modulation configuration, and resulting physical bit rate are shown in Table 3, which also includes the details for optional DR6 and DR7.


As mentioned earlier, Class A LoRaWAN functionality focuses on the end-device, which has the main role in message exchanges: all transactions are started by the end-device, whereas the network server can only transmit in one of two downlink slots, called receive windows (RX1 and RX2, in Figure 2), opened by the end-device, following a previous uplink transmission. Therefore, any message the network server has to transmit after RX2 must wait until the next receive window to be sent.


An end-device uses a different frequency channel for each message transmission, by following a pseudo-random channel sequence. This procedure makes communication robust against interference or other radio propagation impairments (e.g., multipath, etc.).


## 3.2.2. Physical Layer Message Format

LoRaWAN specification defines a physical layer message that comprises a preamble, a physical header (PHDR), a physical header Cyclic Redundancy Check (PHDR_CRC), a physical payload (PHY Payload), and an error detection tail (CRC) [27]. Figure 3 shows the physical layer message structure. PHDR and PHDR_CRC fields have a combined total size of 20 bits. Additionally, 2 bytes of CRC are present only in uplink messages, thus the downlink is optimized for low transmission time.


## 3.2.3. Receive Window Parameters

The DR, the frequency channel and the time between the end of an uplink transmission and the start time for the first and second receive windows (RECEIVE_DELAY1 and RECEIVE_DELAY2, respectively, see Figure 2) are defined in the LoRaWAN regional parameters document [39]. Table 4 shows the main basic physical layer parameters, and their default values.


The DR to be used in the first receive window (RX1) can be set as the uplink DR minus the DR offset RX1 parameter, RX1DROffset, if the latter is equal to or less than the DR of the uplink; otherwise, the DR for the first receive window will be DR0. RX1DROffset can take values in the range of 0 to 5. Since RX1DROffset has a default value of zero, the DR for the first receive window is by default the same one used in the last uplink transmission.


The frequency channel used in the first receive window is the same as the one used for the preceding uplink transmission, while the second receive window uses a fixed frequency and data rate configuration (by default, frequency 869.525 MHz, and DR0). These parameters can be customized in the hardware platform used in the study. However, other platforms (e.g., RN2483, [36,37]) do not support such configurability.


The duration of a receive window has to be at least the time required to effectively detect a downlink preamble [27]. If a preamble is detected during a receive window, the end-device radio remains active until the reception of a complete message. If this is done successfully in the first window, the end-device does not use the second receive window. If a transmission is not detected within a receive window, the radio transceiver and, possibly, the microcomputer chip that support the device will be in an active state, with a significant current consumption, for a certain period of time during the window. This time is an important factor for the end-device lifetime and it is strongly related to the specific transceiver hardware used (see Section 4).


In the hardware platform we have used in this paper, the time spent in preamble detection in a first receive window is determined as the symbol timeout parameter (SymbTimeout), which is set to 8 symbols for DR0 (SF12) and DR1 (SF11), and 12 symbols for the rest of DRs. On the other hand, for the second receive window, a feature called Channel Activity Detection (CAD) is used. This mechanism reduces channel listening time. If no incoming signal is detected, the end-device decides earlier to stop preamble detection, thus saving radio on time and current consumption.


## 3.3. LoRaWAN MAC Layer

## 3.3.1. MAC Message Format

LoRaWAN defines a set of MAC message types that are transmitted as payload of a physical layer message (i.e., are carried in the PHY Payload field). Three basic types of MAC messages are defined: (i) the Join message; (ii) the Confirmed Data message and (iii) the Unconfirmed Data message. The format for a MAC message is shown in Figure 4. The MAC message comprises: (i) the MAC Header (MHDR), which indicates the type of MAC message; (ii) the MAC payload, which can carry application data or a Join message; and (iii) the Message Integrity Code (MIC), which allows a receiver to check the integrity of a MAC message received. On the other hand, data messages can carry MAC commands in the frame payload (FRM Payload), which can also be carried in the frame header (FHDR), depending on the FPort value. MAC commands are intended to configure radio and MAC layer parameters. An important subfield in the FHDR is a bit that allows acknowledging the last Confirmed Data message received.


## 3.3.2. Transmission and Retransmission Procedure

When an end-device transmits an uplink Confirmed Data message, it expects to receive a downlink acknowledgment message in one of the next two receive windows. If the acknowledgment is not received, the end-device retransmits the same message until an acknowledgment is received or until a maximum number of MAC layer transmission attempts for the message (the recommended default number being 8) is reached. Each transmission attempt is done in a different channel, which is randomly selected from the channels available in the subband used. The DR to be used is recommended to follow the next rules. The 1st and 2nd transmission attempts of a confirmed message are done by using the same DR, the 3rd and 4th attempts use the next lower data rate (or DR0 if it was the DR previously used), and so on, until the 8th transmission attempt. After 8 transmission attempts of the same confirmed message without an acknowledgment, the MAC layer should return an error code to the upper layer (i.e., the application layer). Each retransmission is started after an acknowledgment timeout (ACK_TIMEOUT) period, which is initiated at the start time of the last 2nd receive window, and is defined as a random delay between 1 and 3 seconds, by default [39].


## 4. Modeling LoRaWAN End-Device Current Consumption

In this section, we present models of crucial LoRaWAN energy performance parameters such as end-device current consumption, end device lifetime, and energy efficiency of data delivery. We assume a class A end-device that periodically transmits an uplink data message (e.g., a notification that carries a sensor reading). In the models, we consider the impact of bit errors. For the sake of tractability and clarity, we assume a uniform BER that refers to the residual BER after application of physical layer error correcting techniques, equivalent to the residual BER that corresponds to message loss rate due to non-ideal link quality. The section is divided in two subsections, which offer the aforementioned models for unacknowledged and acknowledged transmission, i.e., the transmission of unconfirmed and confirmed data messages, respectively. We develop the models for all DRs that are mandatory (i.e., from DR0 to DR5), as well as for DR6.


## 4.1. Unacknowledged Transmission

Our first goal is modeling the average current consumption of an end-device in the unacknowledged approach, denoted Iavg_unACK. In order to determine this parameter, we first derive a profile of the different states traversed by the end-device, as well as the duration and the current consumed in each state. In order to realistically model the end-device behavior, and without loss of generality, we develop the model based on measurements from a real LoRaWAN testbed. The measurement setup is shown in Figure 5. We use the MultiConnect mDot platform from Multitech [29] as our reference end-device platform for the model, since it is a popular platform, and it is based on the also widely used SX1272 transceiver [33] (see Table 1). While other LoRaWAN end-device platforms might exhibit differences with the mDot platform (e.g., due to their internal architecture), we understand that our model captures the main states of a LoRaWAN end-device. On the other hand, it must be noted that the mDot platform offers low current consumption decrease (of ~3%, and only in the transmit state) when the voltage applied is reduced from 5 V to 3.3 V, the latter being the lowest voltage that allows the device to operate [29]. However, other platforms may not offer the same current consumption stability as battery voltage decreases over time.


In the measurements, the transmit power of the end-device is set to 11 dBm, which is the default value for this parameter. The gateway is a Kerlink LoRa IoT Station platform [40]. Both the end-device and the gateway are located in an indoor scenario, where the distance between the end-device and the gateway is 2 m. In the measurements, data messages carry a frame payload of the maximum size allowed for each DR in the EU band.


We assume a periodic behavior for the LoRaWAN end-device, therefore we model its current consumption during one period. Each period comprises a data message transmission by the end-device (including the related procedures required to enable such transmission), otherwise the device is in sleep mode. Note that, for an end-device in unacknowledged transmission, current consumption is independent of the BER; that is, regardless of whether channel errors take place in the communication, the end-device will consume the same amount of energy for any transmission, since there will not be retransmissions in unacknowledged transmission. Time and current consumption measurement results provided in this section are obtained from several measurements for each tested configuration within a notification period. We found negligible differences within each set of measurements for each configuration.


Figure 6 illustrates the current consumption profile of an unacknowledged transmission performed by the MultiConnect mDot LoRaWAN end-device configured to use DR0 (note that the states traversed and behavior observed are the same for all DRs, except for the duration of some intervals). Table 5 defines and describes the different states involved in an unacknowledged transmission, along with the variables that represent the duration and current consumption of each state. Initially, the end-device is in sleep mode, which is characterized by a current consumption three orders of magnitude below that of the rest of states. When the end-device starts the procedure to perform the transmission, it first wakes up (state 1), next the radio interface is prepared for activity (state 2), and then the end-device transmits the data unit via the radio interface (state 3). After the transmission, the end-device disables radio activity and waits (state 4) until it sets the radio into receive mode and remains in the same state for the duration of the first receive window (state 5). Since no incoming preamble is detected, the first receive window is closed, and the end-device waits (state 6) until the start of the second receive window. During the latter, the end-device radio is turned on for possible incoming data units, until the second receive window is closed due to absence of incoming data (state 7). Note that the shorter duration of the second receive window is due to use of the CAD mechanism (see Section 3.2.3), whereby the end-device stops preamble detection much earlier than in the first receive window if no incoming signal is detected. After that, the radio interface is turned off (state 8), a postprocessing interval follows (state 9), and the end-device executes a turn off sequence (state 10), prior to returning to the sleep state (state 11). One additional consideration is that we have not identified any specific state due to the internal communication, which takes place via Serial Peripheral Interface (SPI), between the main microcontroller and the radio interface of the mDot platform. This is consistent with the submillisecond latency of payload transmission from the microcontroller to the radio interface, for the range of payload sizes in LoRaWAN, that is typical of SPI.


Let TNotif be the time between two consecutive periodic message transmissions performed by the end-device, i.e., the notification period. Let Ti and Ii denote the duration and current consumption of state i in Table 5. Iavg_unACK can thus be calculated as shown in Equation (1):(1)Iavg_unACK= 1TNotif∑i=1NstatesTi·Ii
where Nstates is 11 in unacknowledged transmission. Note that Tsleep can be obtained as:(2)Tsleep=TNotif−Tact
where Tact denotes the sum of the durations of all states related with transmission activities, i.e., all states except the sleep interval:(3)Tact=Twu+Tpre+Ttx+Tw1w+Trx1w+Tw2w+Trx2w+Toff+Tpost+Tseq


The durations Ttx, Trx1w, and Tw2w are variable and depend on the DR in use. Tw2w actually depends on Trx1w, and can be obtained as:(4)Tw2w=RECEIVE_DELAY_2−RECEIVE_DELAY_1−Trx1w


Although Trx2w also depends on the DR, the end-device platform in our experiments uses a fixed setting for the second receive window (which corresponds to DR0), and thus the measured value for Trx2w is also constant. We next provide the models to derive Ttx, Trx1w and Trx2w.


In order to determine the time needed to transmit a data message via the radio interface, Ttx, we take into acount LoRaWAN procedures, LoRa modulation details and the corresponding regional parameters. Ttx can be expressed in terms of the time required to transmit both the preamble and the physical message, denoted Tpreamble and TPHYMessage, respectively, as follows [38]:(5)Ttx = Tpreamble +TPHYMessage


Tpreamble can be obtained as shown next [33]:(6)Tpreamble=Tsym·(Npre+4.25)
where Npre is the programmed number of symbols to be used by the radio transceiver, the actual physical length of the preamble is (Npre + 4.25) [7], and Tsym is the time of a symbol (in seconds), which depends on the SF and the channel bandwidth (BW, in Hz), as follows [38]:(7)Tsym=2SFBW


On the other hand, TPHYMessage (in seconds) can be evaluated similarly:(8)TPHYMessage=Tsym∗NPHY
where NPHY indicates the number of symbols transmitted as the physical message (excluding the preamble), and it can be determined as follows [38]:(9)NPHY=8+max[ceil[28+8·PL+16·CRC−4·SF4·(SF−2·DE)]·(CR+4),0]


In (9), SF corresponds to the spreading factor and can take values from 7 to 12 (which correspond to data rates from DR5 to DR0, respectively); CR denotes the coding rate and can take values from 1 to 4, for 4/5 to 4/8 coding rate, respectively; PL indicates the physical payload length, in bytes. CRC indicates the presence or not of the CRC field in the physical message (CRC is set to 0 if the CRC field is not present; otherwise, CRC is equal to 1); finally, DE, which indicates whether the mechanism to avoid issues regarding drift of the crystal reference oscillator is used or not, takes value 1 for SF12 and SF11 (i.e., it is used for the lowest data rates), and value 0 for the rest of SFs. Equations (5)–(9) can be used to model the duration of both uplink and downlink transmissions (e.g., the latter may correspond to acknowledgments sent in response to uplink data messages, see Table 6).


After modeling Ttx, we proceed to determine the duration of a receive window when no preamble is detected, which occurs in both receive windows in unacknowledged transmission. We next model the behavior of the hardware module used in our experiments in each receive window.


For the first receive window, Trx1w can be determined as follows: (10)Trx1w=Ndsym·Tsym


The end-device stays in receive mode for the duration of Ndsym symbols Ndsym is 8 symbols for SF = 12 and SF = 11, and 12 symbols for the rest of SFs.


For the second receive window, the receiver is active during a fraction of a CAD state (see Section 3.2.3). This fraction has a duration, denoted Trx2w, that can be calculated as shown next: (11)Trx2w=2SF+32BW


After providing the models for determining Ttx, Trx1w and Trx2w, Table 6 summarizes their main values, along with relevant parameter settings used in our end-device platform. For Trx2w, we include the corresponding values for the different DR settings possible. However, in our experiments, only the Trx2w value corresponding to DR0 was used.


Once all variables required to compute Iavg_unACK are determined, we can calculate the theoretical lifetime of a battery-operated end-device that performs unacknowledged transmissions, denoted Tlifetime_unACK, can be obtained on the basis of the battery capacity, Cbattery (expressed in mA·h), as shown next: (12)Tlifetime_unACK= CbatteryIavg_unACK


Note that the above theoretical end-device lifetime calculation assumes an ideal battery with a linear behavior, whereas the characteristics of a real battery degrade over time. Therefore, the calculated end-device lifetime results provided in this paper provide an upper bound on the actual end-device lifetime that can be expected.


Finally, another important performance parameter is the energy cost of data delivery, ECdelivery_unACK, which provides the energy consumed by the end-device per each delivered bit of data payload in unacknowledged mode, as shown below:(13)ECdelivery_unACK= Iavg_unACK·V·TnotifE[ldelivery_unACK]
where V denotes the voltage and E[ldelivery_unACK] indicates the expected amount of data successfully delivered by the end-device per data frame transmitted. Note that in the previous equation, the numerator computes the energy consumed by the device during Tnotif.


Let lpay be the FRM Payload field size (i.e., the amount of data carried in the payload of the data message sent by the end-device), and let lData be the total size of the data message, including all headers. Let b denote the BER as introduced in the first paragraph of Section 4. Since in unacknowledged transmission there is a single transmission attempt, which may suffer bit errrors, E[ldelivery_unACK] is determined as:(14)E[ldelivery_unACK]= lPay·(1−b)lData


Finally, let us assume that collisions may occur, i.e., an end-device message transmission may overlap with messages transmitted by other end-devices connected to the same gateway. Let pcoll be the probability that a data message transmitted by an end-device collides with at least another message transmission. In order to capture impact of collisions on E[ldelivery_unACK], Equation (14) can be extended as follows:(15)E[ldelivery_unACK]= lPay·(1−b)lData·(1−pcoll)


Note that, as already introduced, b corresponds to the residual BER after application of physical layer error correcting techniques, equivalent to the residual BER that corresponds to message loss rate due to non-ideal link quality. In this paper, we assume that CR = 4/5, since it is the default CR in LoRaWAN, except for the 20-bit physical header, where CR = 4/8 is used. For CR = 4/5, a parity bit is added to each group of 4 bits from the physical layer message to be transmitted. Assuming that an error-correcting code is used for CR = 4/8 (e.g., a Hamming code [41]) and the range of BER values for reasonably useful links, and given the short size of the physical header, we approximate the relationship between b and the physical layer BER, denoted bphy, as shown in the next two equations. Let ploss be the probability that a transmitted message is affected by at least one bit error, and therefore the message is lost, and let lphy_header be the 20-bit header size. Therefore:(16)ploss= 1−(1−b)lData=1−(1−bphy)54·(lData−lphy_header)
(17)(1−b)lData=(1−bphy)54·(lData−lphy_header)


## 4.2. Acknowledged Transmission

We next model end-device average current consumption in the acknowledged transmission approach, based on the corresponding current consumption profile of the same hardware platform as in the previous subsection.


In this approach, the end-device may behave in two different ways, since the acknowledgment may be transmitted in the first receive window or in the second one. In our model, we consider both options. We initially assume BER = 0, and we subsequently extend the model in order to consider a non-zero BER. Therefore, the average current consumption of an end-device in acknowledged mode, denoted Iavg_ACK, can be obtained as shown in the next equation:(18)Iavg_ACK= p1win·Iavg_ACK_1+p2win·Iavg_ACK_2
where Iavg_ACK_1 and Iavg_ACK_2 denote the average current consumption of the end-device when the acknowledgment is received in the first and in the second receive window, respectively, and p1win and p2win represent their corresponding probabilities. The LoRaWAN specification offers freedom for network managers and implementers to apply the policy that best suits the requirements of a specific deployment. Therefore, since there is no specific priority by default for the two receive windows, we assume that an acknowledgment may be received by an end-device in the first or in the second receive window with the same probability (i.e., p1win = 0.5 and p2win = 0.5).


We next derive the models for obtaining Iavg_ACK_1 and Iavg_ACK_2. Figure 7 depicts the current consumption profile of an end-device that performs an acknowledged transmission in two different situations: in Figure 7a), the acknowledgment is received in the second window, while in Figure 7b), the acknowledgment is received in the first window. (Note: in our specific scenario, we observed that for DR0-DR3, all ACKs were received in the second window, while for DR4-DR5 all ACKs were received in the first window.)


When the acknowledgment is received by the end-device in the first window, the number of states involved in acknowledged transmission decreases in comparison with unacknowledged transmission, since the end-device does not need to wait for a second receive window (Table 7). On the other hand, duration of the first receive window (Trx1w) and radio off interval (Toff) increase since the acknowledgment needs to be received and subsequently processed. Therefore, Iavg_ACK_1 can be derived by using the same equations used to compute Iavg_unACK (i.e., Equations (1)–(11)), but considering only the states that exist when the acknowledgment is sent in the first receive window (which is equivalent to setting both Tw2w and T2w to 0 in the equations), and the values in Table 7.


In order to compute Iavg_ACK_2, we take into account that behavior of the end-device is similar to that in unacknowledged transmission, since states involved in the corresponding transmission operations are the same, and only two differences can be observed: duration of the second window (T2w) and of the subsequent radio off interval (Toff) are both larger than in the unacknowledged transmission. In fact, the end-device needs to stay in the second receive window for the time needed to receive the acknowledgment, and subsequent operations involve processing of the ACK. Therefore, Iavg_ACK_2 can be obtained by means of the same equations used to compute Iavg_unACK (i.e., Equations (1)–(11)), but using the T2w and Toff values that correspond to acknowledged transmission when an acknowledgment is sent in the second receive window (Table 8).


We next extend the model to compute Iavg_ACK for non-zero BER. We assume that bit errors are uncorrelated.


Let Ik denote the average current consumed by the end-device when it performs k retransmissions (the last one being successfully acknowledged), since the start of the procedures for the first transmission attempt, until the end of the procedures for the k-th retransmission. Let Iact be the average current consumption due to activities related with transmitting a data message (including retransmissions), i.e., all states except the sleep interval. Iact can be computed as:(19)Iact=∑k=0MAX_RETR E[Ik]·pk
where E[Ik] denotes the expected current consumption of an end-device when it has performed k data message retransmissions, pk indicates the probability that the end-device performs k retransmissions of a message, and MAX_RETR denotes the maximum number of message retransmissions by an end-device. The latter is recommended as per the LoRaWAN specification to be set to 7.


E[Ik] can be obtained by using the next equation:
(20)E[Ik]=IOKk·TOKk+∑i=0k(IACK_TO·(TACK_TO−Trx2wi)+ IAi·TAi·pA+IBi·TBi·pB+ICi·TCi·pCpA+pB+pC)TOKk+∑i=1k((TACK_TO−Trx2wi)+TAi·pA+TBi·pB+TCi·pCpA+pB+pC)


In the previous equation, IOKi and TOKi denote the average current consumption and average duration of the activities related with an i-th acknowledged data transmission attempt which is error-free, and can be computed by using (15) and Table 6, Table 7 and Table 8. On the other hand, IACK_TO and TACK_TO correspond to the current consumption and the average duration of the ACK_TIMEOUT interval, respectively. As per our measurements, IACK_TO has the same value as Iw1w, whereas ACK_TIMEOUT is a random variable uniformly distributed between 1 and 3 s. Variables Ixi, Txi and px, where x can be equal to A, B or C, correspond respectively to the average current consumption, duration, and probability of unsuccessful acknowledged data message transmission events defined as follows: A is the event whereby the data message suffers a collision, or it does not suffer a collision but it suffers at least one bit error, and it is equivalent in terms of current consumption and duration to the active part (i.e., all states minus sleep) in unacknowledged transmission; B is the event whereby the data message is successfully received, but the acknowledgment, sent in the first receive window, suffers at least one bit error; and C is the event whereby the data message is successfully received, but the acknowledgment sent in the second receive window, suffers at least one bit error (note that errors in downlink messages can be detected by means of the MIC field). Events B and C are equivalent in terms of current consumption and duration to the active part of successful acknowledged transmission with the acknowledgment in the first and in the second window, respectively. Probabilities pA, pB and pC are determined in Equations (20)–(22). Let lData and lAck denote the total size of the data and acknowledgment messages, respectively. Probabilities pA, pB and pC can then be obtained as follows:(21)pA=pcoll+(1−pcoll)·(1−(1−b)lData)
(22)pB=p1win·(1−pA)·(1−(1−b)lAck)=0.5·(1−pA)·(1−(1−b)lAck)
(23)pC=p2win·(1−pA)·(1−(1−b)lAck)=0.5·(1−pA)·(1−(1−b)lAck)


We next determine pk. To this end, we first derive the probability that an end-device will send an acknowledged message without performing any retransmissions, p0. Then, p0 can be computed as the probability that the data message will not suffer collisions, and neither the data message nor the acknowledgment will suffer errors:(24)p0=(1−b)lData·(1−b)lAck·(1−pcoll)


Based on p0, pk can be found as the probability that only both message and acknowledgment transmissions that correspond to the k-th message retransmission are successful, as follows: (25)pk=(1−p0)k·p0


Note that as per Equation (24), when the end-device reaches the maximum number of retransmissions, if the last data message retransmission is not successful, the corresponding current consumption is not added to Iact computation in Equation (19). Nevertheless, impact of this inaccuracy is negligible for MAX_RETR = 7 and for practical BER values (e.g., up to 10−3). Therefore, we opt to favor simplicity in our model.


On the other hand, for non-zero BER, Tact can be calculated as shown next:(26)Tact=∑k=0MAX_RETR E[Tact_k]·pk
where E[Tact_k] can be determined by using the next equation: (27)E[Tact_k]=TOKk+∑i=1k((TACK_TO−Trx2wi)+TAi·pA+TBi·pB+TCi·pCpA+pB+pC)


Based on Equations (18)–(23), Iavg_ACK can be obtained by considering the active interval and the sleep interval over the notification period, TNotif, as: (28)Iavg_ACK=Iact·Tact+Isleep·(Tnotif−Tact)Tnotif


The previous equation can be used to calculate the theoretical lifetime (i.e., an upper bound on the actual lifetime) of a battery-operated end-device that performs acknowledged transmissions, denoted Tlifetime_ACK, on the basis of the battery capacity, Cbattery (expressed in mA·h), and Iavg_ACK, as shown next: (29)Tlifetime_ACK= CbatteryIavg_ACK


Finally, we model the energy cost of data delivery in acknowledged transmission, ECdelivery_ACK, which provides the energy consumed by the end-device per each delivered bit of data payload in acknowledged transmission, as shown next:(30)ECdelivery_ACK= Iavg_ACK·V·TnotifE[ldelivery_ACK]
where E[ldelivery_unACK] indicates the expected amount of data successfully delivered by the end-device per data frame transmitted in acknowledged transmission.


In acknowledged transmission, the end-device will perform frame transmission retries, upon unsuccessful data frame transmission (either due to collisions or, if no collisions take place, due to bit errors). Therefore, E[ldelivery_ACK] is determined as the probability that the data message is successfully delivered in either the first transmission attempt, or one of the retransmissions for the data message:(31)E[ldelivery_ACK]= lPay·∑k=0MAX_RETR((1−pcoll)·(1−(1−b)lData)+pcoll)k·(1−pcoll)·(1−b)lData


It is worth adding that event A, as defined above, captures the reasons that lead to absence of an acknowledgment in response to the data message sent by the end-device (i.e., collisions or bit errors). However, there is a further possible reason for absence of an acknowledgment requested by an uplink data message, which is duty-cycle limitations, since the gateway also needs to comply with regulations on this subject. Lack of an acknowledgment for this reason is likely when there is a sufficiently high amount of downlink traffic (which may comprise acknowledgments to uplink traffic from end-devices and actual downlink data messages to be sent to end-devices). Let pNoAckDutyCycle denote the probability of absence of an acknowledgment due to duty-cycle limitations. Impact of pNoAckDutyCycle on the end-device energy performance parameters considered in this paper can be modeled by replacing pcoll by pNoAckDutyCycle in Equations (21), (24) and (31). Therefore, the evaluation results on the impact of pcoll on performance that are presented in the next section can serve to understand how energy performance of the end-device depends on pNoAckDutyCycle as well.


## 5. Evaluation

In this section, we use the models derived in Section 4 in order to evaluate LoRaWAN end-device current consumption and lifetime, as well as the energy cost of data delivery. As an additional validation of the evaluation results, we have performed average current consumption measurements of up to 4-min duration (i.e., close to the maximum duration allowed by the power analyzer used), comprising several message transmissions from the end-device, for different configurations in terms of DR, notification period, and acknowledged or unacknowledged transmission. We have found an almost exact match between the average measured current consumption and the one computed by using the analytical models. Note that this is an expected result, since the analytical models have been derived on the basis of measurement results.


The section is divided into three subsections, which focus on each one of the performance parameters mentioned, respectively. Unless explicitly mentioned otherwise, we assume the maximum-sized frame payload for each DR. As it will be shown, this is the most energy-efficient approach per delivered bit, under the assumption that the network comprises a single end-device, and therefore the probability of collision is zero. Nevertheless, the approach of a single-byte payload, which is the least efficient under the same conditions, is also evaluated in the section.


## 5.1. End-Device Current Consumption

## 5.1.1. Unacknowledged Transmission

We calculate the average current consumption of the end-device in unacknowledged transmission by using the values shown in Table 5 and Table 6 and Equations (1)–(11). Figure 8 illustrates the obtained results, as a function of Tnotif and the DR selected. Note that the minimum value for Tnotif is given by the 1% duty-cycle limitation that applies for the mandatory, three-channel sub-band, and it depends on the DR.


As expected, the average current consumption decreases as TNotif increases, since then the sleep intervals have a greater duration, while the duration of the intervals related with communication remains constant. The average current consumption tends asymptotically to the sleep current as TNotif grows.


On the other hand, the average current consumption decreases with the DR, since the duration of transmit and receive intervals is inversely proportional to the bit rate of the DR used. For example, the highest relative difference in terms of current consumption between using DR0 and DR5 is a factor of 2.76, for a notification period of 5 min. However, differences due to the DR used decrease with TNotif.


Finally, note that, in unacknowledged transmission, end-device current consumption is independent of the BER, as the end-device will perform a single transmission attempt of each data unit, regardless of whether it is correctly received by the network server.


## 5.1.2. Acknowledged Transmission

We next use the values shown in Table 6, Table 7 and Table 8 and Equations (18)–(28) to compute the average current consumption of the end-device in acknowledged transmission. In order to compare results of unacknowledged and acknowledged transmission, Figure 9 depicts the results, as a function of TNotif, for various DR settings, and for BER = 0. Since some of the curves of DR2 and DR3 overlap with those of DR4, results for DR2 and DR3 are excluded from Figure 9.


Overall, when BER = 0, the average current consumption of acknowledged transmission follows a tendency with TNotif that is similar to the unacknowledged transmission one: it decreases with TNotif, it tends asymptotically to the sleep current, and it decreases with the DR used.


A remarkable result, which is apparently counterintuitive when considering typical behavior of acknowledged link layer protocols other than LoRaWAN, is the fact that acknowledged transmission yields lower current consumption than that of unacknowledged transmission. Note that in acknowledged transmission, the acknowledgment may be received by the end-device in the first or in the second received window. The latter leads to greater average current consumption than in unacknowledged transmission (since the acknowledgment has to be completely received, as opposed to the duration of the second window where no message is received by the end-device). However, the former involves significantly lower current consumption compared to unacknowledged transmission, since then neither a second receive window nor its previous wait time exist. This leads to an overall average current consumption in acknowledged transmission that is lower than the one in unacknowledged transmission.


The maximum current consumption difference between unacknowledged and acknowledged transmission is ~16%, which is found for DR6 and a notification period of 0.5 min. For other DRs, such maximum difference tends to decrease, down to ~3% for DR0, although such decrease is not monotonical (e.g., the maximum difference for DR4 is lower than that for DR1). Recall that we are considering a frame payload of the highest possible size for each DR, and the maximum frame payload size does not decrease proportionally to the bit rate as the DR decreases.


It is also interesting to consider the case of acknowledgments being always transmitted in the first receive window (i.e., p1win = 1 and p2win = 0). Such conditions lead to the lowest possible LoRaWAN end-device current consumption. In that case, the current consumption in acknowledged transmission decreases by up to 45.1% (for DR5 and a notification period of 1 min), compared to the unacknowledged one. However, such decrease is only significant for low notification periods.


We also evaluate impact of the frame payload size on current consumption. Figure 10 illustrates the average current consumption of an end-device in acknowledged transmission, for a single-byte and also for a maximum-sized frame payload, which provide the lower and the upper bound on average current consumption for a given DR, respectively. The difference between the lower and upper bounds is significant for a low notification period (e.g., ~49% for a notification period of 1 min, and ~59% for a notification period of 5 min, for DR5 and DR0, respectively). Such difference decreases with TNotif, since sleep current then becomes dominant, and it also decreases with the DR, since higher bit rates reduce the relevance of active communication states on average current consumption.


We next evaluate end-device average current consumption for non-zero BER in acknowledged transmission, for BER values up to 10−3, and for DR0 and DR5. Since for DR5, retransmissions may reduce the DR (see Section 3.3.2), and for the sake of a better comparison, for DR5 we consider the same payload size as that of DR0. As shown in Figure 11, for a given DR, a non-zero BER increases end-device average current consumption (up to one order of magnitude for the range of BER values considered), since the end-device performs retransmissions. This effect increases as TNotif decreases, since sleep current consumption then becomes less significant. Note that for a given BER, current consumption for DR5 is lower than that when DR0 is used. For DR5, the lower duration of intervals related with transmission and reception reduces current consumption. This phenomenon is emphasized as BER decreases, since then the number of retries decreases as well.


Finally, we evaluate impact of collisions on the average current consumption of an end-device, for DR0 and DR5, and for pcoll values up to 0.3 (Figure 12). As expected, collisions increase the average current consumption in acknowledged transmission. Increasing pcoll has a slightly greater relative impact on current consumption for DR5 than for DR0. In fact, the contribution to energy consumption of states related with processing and wait times is relatively greater for DR5 (with smaller transmit and receive state duration) than for DR0. Influence of collisions decreases with TNotif, since sleep current becomes dominant.


## 5.2. End-Device Lifetime

Leveraging the average current consumption results obtained in the previous section, we next calculate the theoretical lifetime of a battery-operated end-device by using (12) and (29). We assume a battery capacity of 2400 mAh.


Figure 13 illustrates the end-device lifetime for BER = 0 as a function of TNotif, and the DR, in unacknowledged transmission. Logically, the end-device lifetime behavior is the inverse of the current consumption one presented in Section 5.1. A greater end-device lifetime is obtained with higher TNotif and DR. A maximum value of 5.96 years is obtained with DR6 and TNotif = 1440 min. In addition, it can be shown that regardless of the DR employed, end-device lifetime tends asymptotically to 6.19 years, which can be achieved if the end-device is always sleeping (i.e., TNotif = ∞). Note also that lower DRs lead to lower end-device lifetime, and this effect increases as TNotif decreases. For example, for TNotif = 5 min, end-device lifetime values fall below one year, ranging from 0.26 to 0.83 years (for DR0 and DR5, respectively). If TNotif increases, a lifetime of several years is possible. For example, for TNotif = 60 min and TNotif = 360 min, multi-year lifetimes between 2.13 and 3.76 years, and between 4.55 and 5.52 years, can be achieved, respectively.


We next compare end-device lifetime results of unacknowledged and acknowledged transmission (see Figure 14). As explained in Section 5.1.2., acknowledged transmission follows a tendency very similar to the unacknowledged one. The lower current consumption of acknowledged transmission yields higher end-device lifetime. Similarly to Section 5.1.2, the maximum end-device lifetime difference between unacknowledged and acknowledged transmission is ~16%, for DR5 and a notification period of 0.5 min. For other DRs, such maximum difference tends to decrease, down to ~3% for DR0.


On the other hand, Figure 15 shows the impact of the frame payload size on end-device lifetime. In order to obtain the range of possible end-device lifetime values, 1-byte and also maximum-sized payload are considered for data messages in acknowledged transmission. The corresponding end-device lifetimes are depicted in Figure 15, as a function of TNotif, for different DR settings, and for BER = 0. Only DR0 and DR5 are shown in the figure for the sake of illustration clarity. Impact of the payload size is noticeable only when TNotif is low. For DR0 and TNotif = 5 min, end-device lifetime ranges from 0.27 up to 0.41 years (i.e., a ~52% relative difference), for the payload sizes considered. For DR5 and TNotif = 1 min, end-device lifetime ranges from 0.18 to 0.26 years (i.e., a relative difference of ~49%). However, impact of frame payload size decreases when TNotif increases because sleep state, and thus its current cconsumption, becomes dominant. For example, for a TNotif = 60 min and DR0, end-device lifetime values range from 2.17 to 2.90 years (i.e., 33.4% difference), and from 3.90 to 4.44 years (i.e., a 13.78% difference) for DR5.


Next we evaluate impact of BER on end-device lifetime (Figure 16). Similarly to the observations made in Section 5.1.2, end-device lifetime may decrease by up to one order of magnitude for DR5 and for the range of BER values considered. Impact of BER on end-device lifetime is lower for DR0, and it decreases with TNotif, since end-device lifetime tends asymptotically to the lifetime of an always-sleeping end-device as TNotif increases.


Finally, we also study the impact of pcoll on end-device lifetime (Figure 17). Collisions may significantly reduce end-device lifetime (e.g., by one third for TNotif = 30 min and pcoll = 0.3), and have a greater impact on end-device lifetime for DR5, as expected from the average current consumption analysis in Section 5.1.2.


## 5.3. Energy Cost of Data Delivery

In this subsection, we evaluate the last considered performance parameter, i.e., the energy cost of data delivery for both unacknowledged and acknowledged transmission. We next apply Equations (13), (14), (30) and (31) to determine ECdelivery_unACK and ECdelivery_ACK, respectively. We assume a battery voltage of 3.6 V.


Figure 18 provides the energy cost of data delivery for the unacknowledged approach, as a function of TNotif and the DR used, for BER = 0.


For a given DR, and for BER = 0, the relative difference in energy cost of data delivery between acknowledged and unacknowledged transmission is the same as the difference in terms of current consumption analyzed in Section 5.1.2. However, such difference is only significant for low notification periods, and therefore it is not graphically visible in Figure 16, therefore the figure serves for both unacknowledged and acknowledged approaches.


As shown in Figure 18, for BER = 0, the energy cost of data delivery follows a linear trend as a function of TNotif. As it has been previously shown in Figure 8 and Figure 9, average current consumption, and therefore energy consumption becomes asymptotically constant as a function of TNotif. Therefore, as TNotif increases, the energy consumed by the end-device increases linearly with time, while the number of delivered bits remains constant. Because we are considering the maximum frame payload size allowed by each DR, note that the slope of the curves for DR0-DR2 is the same, since these three DRs allow the same maximum frame payload size (i.e., 51 bytes), the slope for DR3 is lower, since the maximum frame payload size is greater (i.e., 115 bytes), and finally the slope for DR4, DR5 and DR6 is the the lowest, since for these DRs the maximum frame payload size is the largest supported by LoRaWAN (242 bytes). DR0 exhibits slightly greater energy cost of data delivery than DR1, due to the lower bit rate of DR0, which leads to a greater data message and acknowledgment transmit time, as well as receive window duration. The same reasoning applies to the comparison of the energy cost of data delivery of DR1 and DR2. The energy cost of data delivery for DR4 is ~19% and ~40% greater than the one for DR5 and for DR6, respectively, for the lowest notification period, and decreases down to ~1% for both DR5 and DR6 for the highest notification period considered (note that these differences are not visible in Figure 18).


We next evaluate the upper bound on the energy cost of data delivery by considering a frame payload size of 1 byte. Results are shown in Figure 19, along with the ones obtained for a maximum-sized frame payload. As it can be seen, for a given notification period and DR, the energy cost per delivered payload bit for a 1-byte frame payload is roughly two orders of magnitude greater than the one obtained for a maximum-sized frame payload.


We then study the impact of non-zero BER on the energy cost of data delivery, assuming a maximum-sized payload for DR0, and the same payload size for DR5, and considering also unacknowledged and acknowledged data message transmission (see Figure 20). Acknowledged transmission leads to a greater energy cost, by at least one order of magnitude, due to the additional energy consumption of retransmissions, in comparison with the unacknowledged approach. On the other hand, BER has a greater impact on DR5 than on DR0, since the former transmits (and may retransmit) data messages at a higher bit rate, leading to lower energy consumption, which makes retransmissions, and their related overhead, energy-expensive.


We next focus on how collisions influence the energy cost of data delivery (see Figure 21). As expected, collisions increase the energy required per delivered payload bit. In acknowledged transmission, this effect is emphasized, since retransmissions are needed. For example, for DR5, the energy cost of data delivery in acknowledged transmission for Tnotif = 1 min increases by 60% when pcoll increases from 0.1 to 0.3, while in unacknowledged mode, the energy cost per delivered bit increases by 12.8%.


Finally, we analyze and discuss the impact of payload (and thus, message) size on the energy cost per delivered bit in a dense LoRaWAN network, where collisions may occur. Assuming that end-devices perform acknowledged transmissions, network behavior can be modeled by an Aloha access protocol, as an approximation [7]. Under these conditions, the energy cost per delivered bit can be computed as the result of dividing the energy cost of a message transmission (including its retransmissions) by the number of payload bits carried. The energy consumed in a message transmission (including retransmissions) is roughly proportional to the number of transmission attempts per message. In fact, the amount of energy consumed in each retransmission (which includes the energy consumed over ACK_TIMEOUT) is much larger than the energy consumed during the actual transmission state, regardless of the message size, with an accuracy that increases with the DR since transmission time decreases, and with the load offered to the network. On the other hand, in Aloha, the expected number of transmission attempts per message is e2G, where G is the total load offered to the network, and thus the expected energy consumed to deliver a message is a·e2G, where a is the total amount of energy consumed in each transmission attempt. Note that G is proportional to the message size, i.e., lpay + lhead, where lhead denotes the total size of the message headers. Therefore, the energy cost of data delivery under the described conditions can be approximated by (32):(32)ECdelivery≈a·e2Glpay=a·ek·(lpay+lhead)lpay= α·ek·lpaylpay
where α is a constant expressed in Joules, that can be computed by using (33), and k is a constant expressed in bit−1, which depends on the transmission bit rate and on the total message rate offered to the network.


Note that the model presented cannot accurately capture the DR decrease mechanism for retransmissions (see Section 3.3.2), when used, since Aloha assumes all packet transmissions have the same duration. Nevertheless, it allows to qualitatively capture behavior of the energy cost of data delivery as a function of packet size. As shown in Figure 22, impact of payload size on the energy cost per delivered bit depends on the value of k. All curves follow a “U” shape with an optimal payload size that minimizes the energy cost per delivered bit. The “U” shape of the curves can be explained, on the one hand, by the fact that very large messages will lead to high energy cost per delivered bit due to a high number of collisions. On the other hand, messages with very small payload will also lead to high energy cost per delivered bit, because while the number of collisions will be relatively low, the energy cost will be relative to a low amount of delivered bits. As k increases, impact of collisions becomes dominant and the payload size that minimizes the energy cost per delivered bit decreases. Note that for sufficiently low, or sufficiently high, k values, the optimal payload size falls out of the region of valid payload sizes. For example, for a high enough k (e.g., k = 0.1), the corresponding energy cost per delivered bit curve in Figure 22 is a function that grows steadily with payload size.


## 6. Conclusions

In this paper, we have modeled the energy consumption of a Class A LoRaWAN end-device transmitting data messages periodically, considering impact of unacknowledged and acknowledged transmission, DRs, frame payload size and BER. Performance parameters have been end-device average current consumption and lifetime, and energy cost of data delivery. The models have been developed based on measurements performed on prevalent LoRaWAN hardware.


For BER = 0, acknowledged transmission reduces LoRaWAN end-device average current consumption. This happens because an acknowledgment may be sent in the first receive window, whereas unacknowledged transmission involves two receive windows and a larger average current consumption than a transmission acknowledgment in the first receive window. Note that the quantitative difference between energy consumption in acknowledged and unacknowledged transmission for BER = 0 may be platform-specific. In fact, in contrast with the behavior observed with the platform used in this work, the end-device hardware platform might stay in a low consumption mode (e.g., such as the sleep state) during the interval between the first and the second receive windows. On the other hand, for a non-negligible BER, acknowledged transmission leads to greater current consumption than unacknowledged transmission, due to message retries.


For a notification period of 5 min, DR5 leads to a current consumption lower than that of DR0 by a maximum factor of 2.8, whereas a 1-byte frame payload size reduces current consumption by up to a maximum factor of 1.59. For the same notification period, using DR6 (which is not mandatory as per the LoRaWAN specification), current consumption decreases by a factor of 3.18, compared to using DR0. Non-zero BER up to 10−3 may increase current consumption by up to one order of magnitude in acknowledged transmission. Current consumption differences due to the settings considered tend to decrease with the notification period, since sleep current consumption then becomes dominant.


An end-device running on a 2400 mAh battery and sending one message every 5 min can achieve a 1-year lifetime. As the notification period increases, the theoretical end-device lifetime tends asymptotically to roughly 6 years under the conditions considered. However, from our state of the art analysis, we conclude that current LoRaWAN hardware is not as well optimized as that of other low-power technologies. In the latter, sleep current in the order of (or even below) 1 µA is common, which allows multiyear device lifetimes with a button cell battery, of 1 order of magnitude less capacity than the one considered in this study. In contrast, current batteries used for LoRaWAN hardware have a larger size and weight, which in turn has an impact on the physical dimensions and weight of current LoRaWAN devices and limits applicability of current LoRaWAN devices for domains where such dimensions are relevant, such as wearables.


Finally, the energy cost per delivered bit of maximum-sized frame payload transmission is roughly two orders of magnitude lower than the one obtained for the short payload of 1 byte per frame. An end-device operating as a sensor will thus benefit significantly from accumulating readings and sending them at the highest notification period possible. For non-zero BER up to 10−3, acknowledged transmission increases the energy cost of data delivery by up to roughly one and two orders of magnitude, for DR0 and DR5, respectively.

