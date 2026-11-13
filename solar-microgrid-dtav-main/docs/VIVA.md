# Viva preparation

**Why three controllers?** S3 keeps distributed cluster and branch measurements near PV; STM32 owns deterministic local control and display; C3 bridges Wi-Fi without making network code the only controller. This partition is pedagogical and permits fault-isolation demonstrations, not a claim that three chips are always necessary.

**Why LoRa?** It demonstrates low-rate long-range half-duplex sensing independent of Wi-Fi. Packet airtime and legal ERP matter; it is not suitable for the primary fast short-circuit protection loop.

**Why INA226?** Signed high-side shunt measurements offer voltage/current/power with multiple I2C addresses. Accuracy depends on shunt, Kelvin layout and calibration. Cluster monitors alone cannot identify which parallel panel failed.

**Why a twin?** It links energy models, estimates, uncertainty and repeatable fault scenarios. Measurements and estimates stay labelled; the model is simplified and requires calibration before hardware predictions are credible.

**Deterministic control versus DTAV?** The baseline always enforces source availability, interlocked transitions, reserve and priorities. DTAV asks whether an optional fresh measurement could change a supervisory decision and whether its expected value exceeds communication cost. It does not disable essential monitoring.

**Source switching?** A master NO relay opens before a BBM transfer relay selects one regulated12V source. After deadtime and revalidation the master closes; loads restore sequentially. Reverse-feed protection and external fusing remain necessary for failed hardware.

**Panel isolation?** A per-panel high-side eFuse uses integrated opposing MOSFET protection and reverse blocking; the MCU can inhibit it. Hardware current protection operates without I2C. A failed-short switch still needs an independent isolation/protection path.

**Communication failure?** S3 keeps sensing, STM32 keeps local monitoring and power control, C3 reconnects with bounded queues, host marks stale. No laptop or LoRa message is required for battery cutoff.

**Research contribution?** A reproducible implementation/evaluation of decision-value-based selective optional sensing under a shared local safety policy. Evidence consists of measured/simulated report counts, error, decision/detection latency and unserved energy. Novelty and performance gains are hypotheses; this repository does not claim them as established facts.

**Main limitations?** Unknown purchased modules/pack, provisional power-stage passives, no physical commissioning, no authenticated radio, approximate PV/battery model, externally powered controllers, and uncommissioned shared-PV charger/converter interaction.

**Can solar loads and charging run together?** Yes, both protected branches use the entire array. BQ24650 input-voltage regulation reduces charging demand when system load pulls PV voltage down. A signal MOSFET on MPPSET pauses charging during proof, transfer and recovery. This is coordinated sharing requiring analog validation; no panels are permanently reserved for either function.

**What changed at KPV?** COM is PV_COMB, NO enables the solar converter and NC is unused and insulated. MPPT has a dedicated protected input branch. PB10 drives charge inhibition; PB1 senses PV voltage. Six relays and13 INA226 devices remain.
