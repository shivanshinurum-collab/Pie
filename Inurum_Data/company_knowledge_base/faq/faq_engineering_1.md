---
document_id: faq_engineering_1
document_type: FAQ Guide
department: Engineering
owner: Shivansh Kushwah
created_date: 2025-01-15
last_updated: 2026-06-10
version: 1.0
confidentiality: Internal
tags: faq, support, engineering
keywords: engineering faq
aliases: Engineering Practices & Code Guidelines FAQs Part 1
related_documents: training/train_employee_handbook.md
------------------

# Frequently Asked Questions: Engineering Practices & Code Guidelines (Part 1)

## Overview
Curated Q&A list covering Engineering Practices & Code Guidelines at Inurum Technologies - Part 1.

## Detailed Information
### Q01: What is the standard architecture for Flutter apps?
* **Answer:** We follow Clean Architecture using the BLoC state management framework.

### Q02: How do we handle API error codes in mobile apps?
* **Answer:** Implement standardized error wrappers transforming HTTP errors to user messages.

### Q03: What tool is used for API contract testing?
* **Answer:** We use Postman Collections and custom integrations in GitHub Actions.

### Q04: How do we avoid frame drops in Flutter animations?
* **Answer:** Offload complex operations to Dart Isolates and avoid rebuilding heavy widgets.

### Q05: What is the standard database for backend platforms?
* **Answer:** We utilize PostgreSQL for relation data and Redis for cache layers.

### Q06: How do we enforce multi-tenant isolation in PostgreSQL?
* **Answer:** We use Row-Level Security (RLS) policies based on the tenant ID.

### Q07: What cellular module is standard for IoT projects?
* **Answer:** We utilize the Quectel BG95-M3 module for global LPWA projects.

### Q08: How do we handle offline synchronization in mobile apps?
* **Answer:** We use local SQLite queues and commit changes to the backend upon reconnect.

### Q09: What microcontroller is standard for telematics boards?
* **Answer:** We design custom boards leveraging the dual-core ESP32-S3 microcontroller.

### Q10: What communications protocol is used for IoT data?
* **Answer:** MQTT over secure TLS is our default protocol for sensor telematics.

### Q11: How do we implement remote firmware updates?
* **Answer:** We design custom OTA pipelines with dual-partition flash and verification rollbacks.

### Q12: What is the standard coding format for Java services?
* **Answer:** We follow Google Java Style Guide verified via checkstyle plug-ins.

### Q13: How do we manage database migrations in Node.js?
* **Answer:** We use Knex.js or Sequelize migrations committed inside the source repository.

### Q14: What tools are used for static code analysis?
* **Answer:** SonarQube and Dart Analyze are integrated into our GitHub workflows.

### Q15: How do we perform stress testing on REST APIs?
* **Answer:** We run k6 or Apache JMeter load tests simulating concurrent requests.

### Q16: What is the code coverage benchmark for pull requests?
* **Answer:** All pull requests require a minimum of 80% test code coverage.

### Q17: How do we handle sensor noise in telematics boards?
* **Answer:** We implement digital signal processing (DSP) and Kalman filtering algorithms.

### Q18: What software is used for PCB schematic design?
* **Answer:** We use KiCAD and Autodesk EAGLE for circuit board layouts.

### Q19: How do we test PCB signal integrity?
* **Answer:** Through high-frequency oscilloscope testing and RF path tuning jigs.

### Q20: What RTOS is preferred for embedded firmware?
* **Answer:** FreeRTOS and Zephyr RTOS are our standard embedded operating systems.

### Q21: How do we manage code dependencies in Go services?
* **Answer:** We use Go Modules and verify packages in the go.sum file.

### Q22: What is the process to trigger a production release?
* **Answer:** releases require passing the automated CI/CD pipeline and approval from HOD.

### Q23: How do we monitor production microservices?
* **Answer:** We use Prometheus metrics visualized via Grafana dashboards.

### Q24: What is the standard response structure for APIs?
* **Answer:** APIs return JSON payloads with data, status, and error properties.

### Q25: How do we store telemetry datasets?
* **Answer:** We stream data to Kafka queues and ingest into ClickHouse for analytics.


## Related Information
### FAQ Administration
* This FAQ document is updated quarterly.
* Submit new QA requests to Shivansh Kushwah (Engineering).


## FAQ
* **Q: How can I request changes to these FAQs?**
  * A: Contact the owner Shivansh Kushwah via Slack.

## Keywords
Engineering Practices & Code Guidelines, FAQ, questions, help, support
