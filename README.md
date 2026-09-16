# agent_skillz

A small collection of homemade Agent Skills designed to extend the capabilities of the Gemini CLI, Antigravity, and other AI agents.

## Repository
[https://github.com/Steve-t-hill/agent_skillz.git](https://github.com/Steve-t-hill/agent_skillz.git)

## Installation

To use these skills with **Gemini CLI** or **Antigravity**, copy the desired skill folder(s) into your local skills directory:

```bash
cp -r bigquery-graphql ~/.agents/skills/
cp -r bigquery-ca-builder ~/.agents/skills/
cp -r kc-business-glossary-builder ~/.agents/skills/
cp -r kc-data-domain-builder ~/.agents/skills/
cp -r kc-data-product-builder ~/.agents/skills/
```

## Available Skills

### [BigQuery Property Graph Skill (`bigquery-graphql`)](./bigquery-graphql/README.md)
This skill provides expert guidance and an automated agent protocol for transforming existing BigQuery relational datasets into **Labeled Property Graphs (LPG)** and querying them using GQL (ISO standard).

**Key Features:**
- **Relational-to-Graph Translation:** Automatically analyzes BigQuery datasets to infer logical graph topologies (nodes, edges, properties).
- **Statistical Profiling:** Uses `ML.DESCRIBE_DATA` to intelligently collapse lookup tables into node properties and identify super nodes.
- **DDL Generation:** Generates optimized `CREATE PROPERTY GRAPH` statements without data movement.
- **GQL Optimization:** Writes high-performance Graph Query Language (GQL) statements that handle data skew and overcounting.

### [BigQuery CA Builder (`bigquery-ca-builder`)](./bigquery-ca-builder/README.md)
This skill guides the agent in automatically generating configuration and deployment files for a BigQuery Conversational Analytics (BQCA) Agent using the `geminidataanalytics_v1beta` API.

**Key Features:**
- **Automated Artifact Generation:** Generates `config.yaml`, `README.md`, `dump_config.py`, and `update_config.py`.
- **System Instruction & Agent Glossary Orchestration:** Crafts the core persona, data context, query generation rules, agent-level business glossaries, field aggregations, and join relationships.
- **Schema Reference Mapping:** Automatically maps BigQuery tables and datasets into the declarative configuration.
- **Deployment-Ready Output:** Provides the necessary Python scripts to pull and push configurations to Google Cloud.

### [Knowledge Catalog Business Glossary Builder (`kc-business-glossary-builder`)](./kc-business-glossary-builder/README.md)
This skill provides expert guidance and an automated agent protocol for managing Google Cloud Knowledge Catalog Business Glossaries, categories, and terms, and linking terms to physical data assets (e.g., BigQuery tables and columns).

**Key Features:**
- **Ontology & Glossary Management:** Programmatically creates and manages glossaries, categories, and terms with structured metadata.
- **Lineage & Asset Mapping:** Facilitates technical mappings by linking business terms directly to physical BigQuery tables and columns.
- **CLI Utility Integration:** Equips the agent with the `glossary_manager.py` CLI tool to interact with the Knowledge Catalog REST API.
- **Semantic Audit & Relationships:** Helps identify synonyms and related terms to create strong linkages between business concepts.

### [Knowledge Catalog Data Domain Builder (`kc-data-domain-builder`)](./kc-data-domain-builder/README.md)
This skill provides expert guidance, Domain-Driven Design (DDD) heuristics, and an automated agent protocol for creating, managing, authorizing, and binding Dataplex Data Domains in Google Cloud Knowledge Catalog.

**Key Features:**
- **Domain-Driven Design (DDD):** Categorizes physical datasets into Source-Oriented and Consumer-Oriented bounded contexts.
- **Hierarchical Subdomains:** Models multi-level business domains (up to 5 nesting levels).
- **3-Step Resource Binding Workflow:** Automates domain principal (`policyMember`) extraction, resource authorization, and binding for BigQuery datasets and GCP projects.
- **CLI Utility Integration:** Equips the agent with `domain_manager.py` to manage domains, IAM policies, bindings, and scoped semantic search.

### [Knowledge Catalog Data Product Builder (`kc-data-product-builder`)](./kc-data-product-builder/README.md)
This skill provides expert guidance, Product Manager heuristics, and an automated agent protocol for curating, bundling, securing, and governing Dataplex Data Products in Google Cloud Knowledge Catalog.

**Key Features:**
- **Consumption-First Product Design:** Packages data assets around specific business use cases and consumer outcomes.
- **Cross-Domain Packaging:** Unifies disparate BigQuery tables/views and Cloud Storage buckets spanning different Data Domains.
- **Persona-Based Access Groups:** Abstracts fine-grained infrastructure IAM into consumer roles (e.g., Analyst, Data Scientist).
- **Governance & Approval Workflows:** Streamlines change requests (`requestAccess`), reviews, approvals, and rejections.
- **Contracts & Catalog Aspects:** Enriches product entries with `refresh-cadence` SLA contracts and `overview` documentation.
- **CLI Utility Integration:** Equips the agent with `product_manager.py` to manage products, assets, access groups, change requests, and aspects.

---

## Usage

Once installed in `~/.agents/skills/`, these skills can be activated within a session using the `activate_skill` tool by referencing their name (e.g., `bigquery-graphql`, `bigquery-ca-builder`, `kc-business-glossary-builder`, `kc-data-domain-builder`, or `kc-data-product-builder`).

---

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) and [NOTICE](NOTICE) files for details.

