---
document_id: tech_infrastructure
document_type: Technical Specification
department: Engineering
owner: Shivansh Kushwah
created_date: 2025-01-15
last_updated: 2026-06-10
version: 3.1
confidentiality: Confidential
tags: tech, architecture, database, cloud
keywords: infrastructure documentation, systems design
aliases: Infrastructure Documentation
related_documents: sops/sop_deployment.md
------------------

# Technical Specification: Infrastructure Documentation

## Overview
Detailed technical blueprints, layouts, schemas, and configurations for Infrastructure Documentation at Inurum Technologies.

## Detailed Information
### System Architecture & Specs
AWS cloud layout, EC2 VPC configs, Docker setups, and subnets.
Built using industry standards: AWS, Docker, Kubernetes, Terraform, PostgreSQL, Redis, and OpenSearch.

### Core Implementation
* **Cloud Architecture:** Hosted on AWS EKS and EC2 nodes.
* **Security & Auth:** JWT authentication via OAuth2 gateways.
* **Telematics Logs:** Ingestion via MQTT brokers (Mosquitto/EMQX).
* **Database Scaling:** Row-level security for tenant data.

### Configuration Parameters
```json
{
  "environment": "production",
  "auth_token_reference": "IN-7742-XP",
  "database_port": 5432,
  "redis_cache_ttl": 3600
}
```


## Related Information
### Deployment Requirements
* Run standard deployment SOP: [sop_deployment.md](../sops/sop_deployment.md).
* Verify configuration variables in Terraform staging files before executing `apply`.


## FAQ
* **Q: Where can I find API tokens?**
  * A: All secrets must be fetched from the AWS Secrets Manager.
* **Q: How often are database backups executed?**
  * A: Automated database backups run every 6 hours with cross-region sync.


## Keywords
Infrastructure Documentation, technology, AWS, kubernetes, configuration
