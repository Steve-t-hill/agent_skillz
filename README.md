# steves_agent_skillz

A small collection of homemade Agent Skills designed to extend the capabilities of the Gemini CLI, Antigravity, and other AI agents.

## Installation

To use these skills with **Gemini CLI** or **Antigravity**, copy the desired skill folder(s) into your local skills directory:

```bash
cp -r bigquery-graphql ~/.agents/skills/
```

## Available Skills

### [BigQuery Property Graph Skill (`bigquery-graphql`)](./bigquery-graphql/README.md)
This skill provides expert guidance and an automated agent protocol for transforming existing BigQuery relational datasets into **Labeled Property Graphs (LPG)** and querying them using GQL (ISO standard).

**Key Features:**
- **Relational-to-Graph Translation:** Automatically analyzes BigQuery datasets to infer logical graph topologies (nodes, edges, properties).
- **Statistical Profiling:** Uses `ML.DESCRIBE_DATA` to intelligently collapse lookup tables into node properties and identify super nodes.
- **DDL Generation:** Generates optimized `CREATE PROPERTY GRAPH` statements without data movement.
- **GQL Optimization:** Writes high-performance Graph Query Language (GQL) statements that handle data skew and overcounting.

---

## Usage

Once installed in `~/.agents/skills/`, these skills can be activated within a session using the `activate_skill` tool by referencing their name (e.g., `bigquery-graphql`).

