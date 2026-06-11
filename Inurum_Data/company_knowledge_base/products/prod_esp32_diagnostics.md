---
document_id: prod_esp32
document_type: Product Document
department: Engineering
owner: Shivansh Kushwah
created_date: 2025-01-15
last_updated: 2026-06-10
version: 1.5
confidentiality: Internal
tags: product, hardware, iot, diagnostics
keywords: diagnostics board esp32-s3, hardware specifications
aliases: Diagnostics Board ESP32-S3
related_documents: technical_docs/tech_architecture.md
------------------

# Product Sheet: Diagnostics Board ESP32-S3

## Overview
Hardware specifications, firmware parameters, and integrations for the Diagnostics Board ESP32-S3 product designed by Inurum Technologies.

## Detailed Information
### Technical Specifications
Compact diagnostics hardware board designed to extract vehicle telemetry.

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
Diagnostics Board ESP32-S3, product, hardware, ESP32, Quectel
