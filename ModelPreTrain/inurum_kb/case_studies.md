# Inurum Technologies - Engineering Case Studies

This document details five featured project case studies illustrating Inurum Technologies' experience in hardware development, embedded firmware, mobile apps, and scalable cloud architectures.

---

## 1. ELIoT — AI Multi-Sensor Plant Intelligence
* **Client:** GardenStuff (Italy)
* **Platforms:** Android, iOS, Web
* **Development Timeline:** 8 Months
* **Current Status:** Successfully Launched via Kickstarter Campaign
* **Product Category:** Consumer IoT, Smart Home, AgTech

### Technical Overview & Features
ELIoT is an IoT multi-sensor plant monitoring system built into a modular plant wall. It performs an initial 96-hour environmental survey of the target room or space, sampling 5 distinct environmental sensors every 6 minutes:
* Ambient Temperature
* Light Intensity & Spectrum
* Air Humidity
* Soil Moisture
* Soil pH

The edge sensors feed data into a local processor that uses predictive analytics to recommend the exact plant species and soil types best suited to thrive in that specific microclimate.

### Companion App & UX
* **Live Telemetry:** Dynamic dashboards displaying soil moisture, pH, and light levels in real-time.
* **Automated Care Plans:** Push notification alerts reminding users when to water, fertilize, or adjust ambient light.
* **Smart Home Integration:** Custom integrations with Amazon Alexa and Google Assistant for voice-activated diagnostics.
* **Power Management:** Custom hardware designed to run for up to 6 months on a single charge. Features wireless charging via the Qi standard.

---

## 2. SmartStarter — Semi-Truck Remote Engine Controller
* **Industry:** Commercial Trucking & Logistics
* **Market Focus:** Canada & North America (Sub-zero climate optimizations)
* **Platforms:** iOS, Android, Cloud Backend
* **Product Category:** Fleet Telematics, Connected Vehicles

### Technical Overview & Features
SmartStarter is an enterprise fleet solution that enables remote starting, tracking, and diagnostics of semi-trucks. The system includes a custom-engineered plug-and-play PCB module that connects directly to OEM truck harnesses, maintaining vehicle warranty without requiring wiring cuts.

### Core Capabilities
* **Remote Ignition Control:** Remote start/stop from the mobile app with safety runtime limits (configurable from 10 minutes to 1 hour).
* **Auto-Start Safety Loops:** Automatic engine startup triggered by low battery voltage or critical low temperatures to prevent engine block freezing.
* **Pre-Trip Safety Inspections:** Scans 6 vital parameters before releasing remote control: Oil pressure, Coolant level, Parking brake state, Gearbox position (must be Neutral), Battery voltage, and Hood sensor (must be Closed).
* **Engine Protection Loop:** Auto-shutdown mechanism triggered if oil pressure drops or engine coolant temperature exceeds safety thresholds during remote run.
* **GPS Tracking & Recovery:** High-accuracy GPS tracking with cellular geofencing and theft-recovery mode.

---

## 3. Fruitrack — Agricultural IoT Telemetry
* **Client:** Wisecrop (Portugal)
* **Platforms:** iOS, Android, Web Dashboard, Handheld IoT scanners
* **Development Timeline:** 8 Months
* **Current Status:** Live & Scaled in production, managing hundreds of agricultural workers daily
* **Product Category:** AgTech, Enterprise SaaS, Workforce Management
* **Google Play App Link:** [Wisecrop Fruitrack](https://play.google.com/store/apps/details?id=com.wisecrop.fruitrack)

### Technical Overview & Features
Fruitrack is a worker productivity and harvest telemetry tracking system designed for large agricultural estates. Built as a cross-platform Flutter mobile application, it allows supervisors to track task times, harvest weights, and logging locations.

### Key Innovations
* **Offline-First Synchronization:** Uses a robust local SQLite queue database on the device. All data is saved locally offline and automatically committed to AWS cloud backends when network coverage is restored.
* **Rapid Data Entry:** UI optimized for field conditions, reducing harvest entry logging time to under 10 seconds per worker (an 8x speed improvement over legacy tools).
* **Supervisor Dashboard:** Live analytics display tracking total harvest volumes, parcel-by-parcel productivity logs, and individual worker metrics.

---

## 4. Current Detection Sensor System (Industrial IoT)
* **Domain:** Heavy Industrial Welding Machinery
* **Platforms:** Embedded Firmware, Wi-Fi Communications, Cloud Analytics
* **Product Category:** Industrial IoT (IIoT), Predictive Maintenance

### Technical Overview & Features
This Industrial IoT solution was engineered to monitor and analyze welding pulses from heavy machinery without altering existing wiring or violating factory safety certifications.

### Core Technical Features
* **Non-Invasive Sensing:** Utilizes a split-core Hall Effect current sensor clamped around the welding machine's output cable, requiring zero wiring cuts.
* **Universal Current Profiling:** Detects both AC and DC welding currents, supporting resistive, MIG, TIG, and spot welding machines.
* **Pulse Feature Extraction:** The onboard microcontroller samples the current at high frequencies to extract and calculate 9 distinct data fields per welding pulse:
  1. Peak current
  2. Average current
  3. Pulse duration
  4. Residual current
  5. Current variation profile
  6. Pulse count
  7. Power factor
  8. Energy consumed
  9. Thermal load index
* **Cloud Ingestion:** Transmits JSON payloads via HTTP POST over secure local Wi-Fi networks.
* **Local Buffer Storage:** Implements local flash buffers with auto-retry mechanisms to prevent data loss during Wi-Fi dropouts.
* **Pulse Curve Profiling:** Transmits high-resolution wave shape data to the cloud for automated weld quality profiling and early-stage defect detection.

---

## 5. Mobile Refrigeration Control System
* **Domain:** Cold-Chain Logistics & Asset Tracking
* **Stack:** ESP32 Microcontroller, Quectel Cellular Modules, Cloud IoT Ingestion
* **Product Category:** Telematics, Cold-Chain Management

### Technical Overview & Features
This telematics solution is designed for cargo refrigeration units on long-haul transport vehicles to preserve temperature-sensitive goods.
* **Controller:** Custom ESP32-based controller logging temperature, door open sensors, and power grid status.
* **Cellular Bridge:** Integrated Quectel modules transmit GPS telemetry and environmental status over global cellular networks.
* **Cloud Platform:** Real-time ingestion system mapping refrigeration temperatures, triggering SMS/email alerts if temperatures stray from target thresholds, and enabling remote control (adjusting setpoints, defrost cycles) directly from dispatch centers.
