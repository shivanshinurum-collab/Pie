# Inurum Technologies - Technical Blog Insights & Knowledge Base

This document extracts core technical blueprints and architecture summaries from Inurum Technologies' engineering blog posts, focusing on vehicle telematics, cellular IoT, and regulatory hardware devices.

---

## 1. Vehicle Diagnostics & Telematics with ESP32-S3
This technical article outlines how Inurum designed a compact, multi-protocol vehicle diagnostics board using the ESP32-S3 microcontroller to extract real-time engine telemetry.

### Core Architecture & Hardware Design
* **Microcontroller:** ESP32-S3 dual-core processor. Configured to handle concurrent CAN bus traffic processing, GPS tracking, and wireless communication.
* **Compact Footprint:** Physical board dimensions are optimized to 56mm x 55mm for integration in vehicle dashboard spaces.
* **Integrated GPS:** Features the Quectel LC86G GPS/GNSS module for high-sensitivity, multi-constellation location tracking.
* **Connectivity:** Supports Bluetooth 5 (BLE) for local diagnostic pairings and Wi-Fi 4 (802.11 b/g/n) for warehouse/depot auto-syncs.

### Diagnostic Protocol Integrations
The board bridges three distinct vehicle communications protocols onto a single hardware layout:
1. **SAE J1939 (Heavy-Duty Vehicles):** Interfaced directly with the CAN bus transceiver to read engine RPM, coolant temperature, fuel rate, and trouble codes (DTCs) from commercial semi-trucks.
2. **OBD-II (Light/Medium Passenger Vehicles):** Decodes standard automotive diagnostic parameters (PIDs) using ISO 15765-4 CAN protocols.
3. **SAE J1708 (Legacy Commercial Fleet Systems):** Supports older commercial vehicles by implementing serial communications over RS-485/Modbus physical transceivers.

---

## 2. Global Deployments: Quectel BG95 for Cellular IoT
This entry highlights the integration of the Quectel BG95-M3 cellular module in low-power, wide-area (LPWA) internet-of-things applications across global environments.

### Board Specifications
* **Primary Cellular Module:** Quectel BG95-M3, supporting LTE Cat M1 (eMTC), LTE Cat NB2 (NB-IoT), and integrated high-accuracy GPS/GNSS.
* **Form Factor:** Optimized 50mm x 50mm board design.
* **Processor Modes:** Supports execution using the BG95's internal ThreadX-based MCU. This eliminates the cost and footprint of an external host microcontroller for simple sensor logging tasks.
* **Onboard Sensor Suite:** Directly integrates ambient humidity, temperature, and atmospheric pressure sensors.
* **Power Supply Flexibility:**
  * Micro-USB port (5V input / debugging interface)
  * 3.7V Lithium-Polymer rechargeable battery circuit
  * Dedicated 5V solar panel charging port for remote outdoor deployments.

### Global Use-Case Implementations
Inurum has customized and deployed this BG95 board in five global locations:
* **India (Cold-Chain Logistics):** Placed in mobile refrigeration trucks to track cabin temperatures, GNSS coordinates, and compressor metrics.
* **Germany (Automated Retail):** Embedded in smart vending machines to monitor real-time inventory stock levels and process online cashless payments.
* **USA (Fleet Telematics):** Connected to vehicle OBD/CAN ports to parse engine telematics data and relay it to cloud databases.
* **Nigeria (Utility Infrastructure):** Deployed on electrical power distribution lines to track power availability and grid drops from generation hubs to local substations.
* **Israel (Industrial Automation):** Interfaces with Programmable Logic Controllers (PLCs) in manufacturing plants to provide remote cloud diagnostics.

---

## 3. Electronic Logging Devices (ELD) & NT-11 Hardware
This guide explains the architecture of compliance-level Electronic Logging Devices (ELD) required by transportation authorities for tracking Hours of Service (HOS) in commercial fleets.

### Ecosystem Components
The Inurum ELD solution consists of three integrated components:
1. **Onboard Telematics Hardware (NT-11 / PT-30 / PT-40):** Plugs directly into the vehicle's diagnostic port (9-pin or 6-pin Deutsch connector) to log operational metrics.
2. **Mobile App:** Connects to the OBD hardware over Bluetooth Low Energy to calculate remaining driving limits, manage daily logs, and display compliance data during roadside inspections.
3. **Web-Based Fleet Administration Panel:** Aggregates logs, monitors vehicle safety inspections, and generates compliance reports for fleet managers.

### The NT-11 Hardware Unit
The NT-11 is Inurum's proprietary, high-durability ELD hardware unit designed to survive extreme cabin environments.
* **Data Log Capture:** Continuously queries engine hours, vehicle odometer, vehicle speed, engine start/stop events, and active diagnostic codes.
* **Universal Compatibility:** Firmware is designed to automatically negotiate and support various third-party hardware modules (such as PT-30 and PT-40 models) to ensure retrofitting capability across mixed commercial fleets.
