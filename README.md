# agent_skillz

A small collection of homemade Agent Skills designed to extend the capabilities of the Gemini CLI, Antigravity, and other AI agents.

## Repository
[https://github.com/Steve-t-hill/agent_skillz.git](https://github.com/Steve-t-hill/agent_skillz.git)

## Installation

To use these skills with **Gemini CLI** or **Antigravity**, copy the desired skill folder(s) into your local skills directory:

```bash
cp -r bigquery-graphql ~/.agents/skills/
cp -r bigquery-ca-agent-builder ~/.agents/skills/
```

## Available Skills

### [BigQuery Property Graph Skill (`bigquery-graphql`)](./bigquery-graphql/README.md)
This skill provides expert guidance and an automated agent protocol for transforming existing BigQuery relational datasets into **Labeled Property Graphs (LPG)** and querying them using GQL (ISO standard).

**Key Features:**
- **Relational-to-Graph Translation:** Automatically analyzes BigQuery datasets to infer logical graph topologies (nodes, edges, properties).
- **Statistical Profiling:** Uses `ML.DESCRIBE_DATA` to intelligently collapse lookup tables into node properties and identify super nodes.
- **DDL Generation:** Generates optimized `CREATE PROPERTY GRAPH` statements without data movement.
- **GQL Optimization:** Writes high-performance Graph Query Language (GQL) statements that handle data skew and overcounting.

### [BigQuery CA Agent Builder (`bigquery-ca-agent-builder`)](./bigquery-ca-agent-builder/SKILL.md)
This skill guides the agent in automatically generating configuration and deployment files for a BigQuery Conversational Analytics (BQCA) Agent using the `geminidataanalytics_v1beta` API.

**Key Features:**
- **Automated Artifact Generation:** Generates `config.yaml`, `README.md`, `dump_config.py`, and `update_config.py`.
- **System Instruction Orchestration:** Crafts the core persona, data context, and query generation rules for the BQCA agent.
- **Schema Reference Mapping:** Automatically maps BigQuery tables and datasets into the declarative configuration.
- **Deployment-Ready Output:** Provides the necessary Python scripts to pull and push configurations to Google Cloud.

---

## Usage

Once installed in `~/.agents/skills/`, these skills can be activated within a session using the `activate_skill` tool by referencing their name (e.g., `bigquery-graphql` or `bigquery-ca-agent-builder`).

