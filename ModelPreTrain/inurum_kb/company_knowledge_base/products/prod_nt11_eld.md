---
document_id: prod_nt11
document_type: Product Document
department: Engineering
owner: Shivansh Kushwah
created_date: 2025-01-15
last_updated: 2026-06-10
version: 1.5
confidentiality: Internal
tags: product, hardware, iot, diagnostics
keywords: nt-11 eld unit, hardware specifications
aliases: NT-11 ELD Unit
related_documents: technical_docs/tech_architecture.md
------------------

# Product Sheet: NT-11 ELD Unit

## Overview
Hardware specifications, firmware parameters, and integrations for the NT-11 ELD Unit product designed by Inurum Technologies.

## Detailed Information
### Technical Specifications
High-durability Electronic Logging Device designed for commercial truck cabins.

* **Dimensions:** 56mm x 55mm (Diagnostics), 50mm x 50mm (Quectel LPWA).
* **Protocols Interfaced:** SAE J1939, OBD-II, SAE J1708.
* **Sensors Integrated:** Humidity, temperature, atmospheric pressure.
* **Power Supply:** Micro USB, 3.7V rechargeable battery, 5V solar connector.

### Core Capabilities
* Bluetooth 5 (BLE) for local diagnostic pairings.
* Integrated GPS/GNSS high-sensitivity tracker (Quectel LC86G).
* Hardware-level security storage via cryptographic chip.


## Related Information
### Applications & Projects
* Widely used in: [proj_002_smartstarter_fleet_engine_control.md](../projects/proj_002_smartstarter_fleet_engine_control.md).
* Refer to technical guide: [tech_architecture.md](../technical_docs/tech_architecture.md).


## FAQ
* **Q: What certification does this hardware hold?**
  * A: Certified under FCC, CE, and compliant with North American ELD requirements.
* **Q: Can it run on ThreadX MCU without host CPU?**
  * A: Yes, ThreadX internal MCU execution is supported.


## Keywords
NT-11 ELD Unit, product, hardware, ESP32, Quectel
