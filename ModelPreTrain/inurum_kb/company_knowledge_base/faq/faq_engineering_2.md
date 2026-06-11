---
document_id: faq_engineering_2
document_type: FAQ Guide
department: Engineering
owner: Shivansh Kushwah
created_date: 2025-01-15
last_updated: 2026-06-10
version: 1.0
confidentiality: Internal
tags: faq, support, engineering
keywords: engineering faq
aliases: Engineering Practices & Code Guidelines FAQs Part 2
related_documents: training/train_employee_handbook.md
------------------

# Frequently Asked Questions: Engineering Practices & Code Guidelines (Part 2)

## Overview
Curated Q&A list covering Engineering Practices & Code Guidelines at Inurum Technologies - Part 2.

## Detailed Information
### Q26: What is the maximum response latency target for APIs?
* **Answer:** Average API response latency must remain below 50ms under standard loads.

### Q27: How do we secure BLE communications?
* **Answer:** We use encrypted BLE pairing keys and dynamic handshake tokens.

### Q28: What is the protocol for heavy-vehicle telematics?
* **Answer:** We implement SAE J1939 protocols to read CAN-bus telemetry.

### Q29: How do we handle passenger car diagnostics?
* **Answer:** We decode standard OBD-II parameter IDs (PIDs) using ISO 15765-4 CAN.

### Q30: What RS-485 standard is used for legacy vehicles?
* **Answer:** We use SAE J1708 serial protocols over Modbus transceivers.

### Q31: How do we verify battery optimization on IoT hardware?
* **Answer:** We measure current consumption in sleep states using specialized power monitors.

### Q32: What tools are used to document APIs?
* **Answer:** We use OpenAPI / Swagger specifications compiled in the code repositories.

### Q33: How do we handle duplicate HTTP requests?
* **Answer:** Implement idempotency keys on the server and check keys in Redis.

### Q34: What cache strategy is used for hot records?
* **Answer:** Cache-aside strategy leveraging Redis with configured TTL values.

### Q35: How do we isolate developer sandboxes on AWS?
* **Answer:** We use AWS Organizations with separate sandbox accounts per engineer.

### Q36: What docker base image is preferred?
* **Answer:** We use minimal alpine or distroless images to reduce vulnerability footprints.

### Q37: How do we verify JWT signatures?
* **Answer:** Gateways check signatures using public keys fetched from our JWKS endpoint.

### Q38: What is the backup target for PostgreSQL?
* **Answer:** Hourly incremental backups and weekly full backups saved to AWS S3.

### Q39: How do we implement search features in databases?
* **Answer:** We sync data changes to OpenSearch clusters using CDC pipelines.

### Q40: What is the standard unit test framework for Dart?
* **Answer:** We use the standard test package in Dart SDK with mocktail for mocks.

### Q41: How do we manage secrets in Kubernetes?
* **Answer:** We use External Secrets Operator synced with AWS Secrets Manager.

### Q42: What is the standard container registry?
* **Answer:** AWS Elastic Container Registry (ECR) with automated security scanning.

### Q43: How do we perform database schema updates?
* **Answer:** Migrations are run during low-traffic windows using blue-green models.

### Q44: What is the testing procedure for firmware?
* **Answer:** Hardware-in-the-loop (HIL) automated test setups in our laboratory.

### Q45: How do we track memory leaks in Flutter?
* **Answer:** We use Flutter DevTools memory profiling tools during QA passes.

### Q46: What is the logging standard for backend services?
* **Answer:** Structured JSON logging containing timestamp, trace ID, and severity level.

### Q47: How do we handle rate limiting on public APIs?
* **Answer:** We enforce rate limiting at the API gateway layer using token bucket rules.

### Q48: What tool is used for automated regression tests?
* **Answer:** We write integration test suites using Flutter Driver and Appium.

### Q49: How do we secure server-to-server communications?
* **Answer:** Through mutual TLS (mTLS) configurations inside our service mesh.

### Q50: Where are technical coding standards published?
* **Answer:** standards are detailed in the Engineering Handbook inside the training section.


## Related Information
### FAQ Administration
* This FAQ document is updated quarterly.
* Submit new QA requests to Shivansh Kushwah (Engineering).


## FAQ
* **Q: How can I request changes to these FAQs?**
  * A: Contact the owner Shivansh Kushwah via Slack.

## Keywords
Engineering Practices & Code Guidelines, FAQ, questions, help, support
