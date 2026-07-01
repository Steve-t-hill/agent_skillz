---
name: bigquery-ca-builder
description: |
  Expert guidance and automated agent protocol for generating configuration and deployment artifacts for BigQuery Conversational Analytics (BQCA) Agents.
  This skill automates the creation of 'config.yaml', system instructions, agent-level glossaries, table schema metadata, join relationships, and Python-based synchronization scripts to enable NL2SQL and GQL capabilities against existing datasets and Property Graphs.
  Use this skill when:
    1. Building a new conversational analytics agent from scratch.
    2. Generating or updating system instructions, agent-level glossaries, or table relationships for an NL2SQL agent.
    3. Scaffolding deployment scripts for BQCA lifecycle management.
license: Apache-2.0
metadata:
  version: v2
  publisher: Steve Thill
---

# BigQuery Conversational Analytics (BQCA) Agent Scaffolding

## TL;DR
This skill guides the agent in automatically generating configuration and deployment files for a BigQuery Conversational Analytics (BQCA) Agent using the `geminidataanalytics_v1beta` API. 

Use this skill when a user asks to "build a conversational analytics agent", "create a BQCA agent", "add agent-level glossary terms", or "generate a config.yaml for an NL2SQL agent" against an existing BigQuery dataset or Property Graph.

## The Output Artifacts
When invoked, the agent MUST generate a directory (e.g., `bqca_[name]_agent`) containing the following 4 files:

1.  **`README.md`**: Documentation explaining the agent's purpose, the required Python packages (`requests`, `google-auth`, `pyyaml`), and instructions on using the Python scripts.
2.  **`config.yaml`**: The declarative configuration defining the agent's identity, system instructions (persona, context, rules, examples), agent-level glossaries, table & field metadata, join relationships, and dataset schema references.
3.  **`dump_config.py`**: A Python script to download the live config to `config.yaml`.
4.  **`update_config.py`**: A Python script to push the local `config.yaml` to GCP.

## System Instructions & Agent-Level Glossaries (The Heart of `config.yaml`)
The `staging_context` block inside `config.yaml` (under `data_analytics_agent`) supports both unstructured markdown instructions (`system_instruction`) and structured metadata blocks (`glossaries`, `tables`, `relationships`, `additional_descriptions`):

### 1. `system_instruction` Markdown Format
```markdown
1. Persona & Role
You are the Senior [Domain] Data Analyst for the {your-gcp-project} project. Your role is to translate natural language questions into precise GoogleSQL/GQL queries against the [Dataset] dataset.

2. Data Context (Project: [Project ID])
You have access to [X] core tables in the [Dataset] dataset. 
[Insert Markdown Table listing Table Name, Primary Join Key, and Key Business Attributes]

3. Query Generation Rules (BigQuery)
* Dataset Path: Always use the fully qualified path: ` [Project ID].[Dataset].<table_name> `.
* Graph Queries: If querying a property graph, use `GRAPH [Project ID].[Dataset].[Graph Name] MATCH ...`.
* KPI Definitions: [Define specific formulas, e.g., Gross Margin = SUM(profit)/SUM(sales)]
* Security: Only generate SELECT statements. Never generate INSERT, UPDATE, DELETE, or DROP.

4. Interaction Protocol
1. Analyze Intent: Identify the core business metric.
2. Generate SQL/GQL: Provide the query first.
3. Summarize Insight: Provide a one-sentence "Executive Summary" explaining the business impact.

5. Example Queries for Reference
* [Example 1: Short description and SQL/GQL snippet]
* [Example 2: Short description and SQL/GQL snippet]
```

### 2. Agent-Level Glossaries & Structured Context
In addition to `system_instruction`, agent-specific business terms, column aggregations, table relationships, and supplemental rules can be defined directly in the configuration:

* **Agent Glossaries (`glossary_terms`)**: Defines business terms and KPIs specific to this agent. In the REST API (`geminidataanalytics_v1beta`), `staging_context.glossary_terms` (`glossaryTerms`) directly populates the dedicated **Glossary (X)** UI section in the BigQuery Console Agent Editor. Each entry must contain `display_name` and `description`.
* **Table & Field Specifications (`tables`)**: Defines default or common column aggregations (e.g., `SUM`, `AVG`).
* **Table Relationships (`relationships`)**: Defines join relationships between tables including join types (`inner`, `left`, etc.), cardinalities (`one-to-many`, etc.), and join columns.
* **Additional Descriptions (`additional_descriptions`)**: Captures general operational rules or context not covered elsewhere.

## Template Files
Use the following templates to generate the required files. Replace placeholders (like `[PROJECT_ID]`, `[AGENT_ID]`, `[DATASET_ID]`) with actual values based on the user's context.

### 1. `config.yaml` Template
```yaml
name: projects/[PROJECT_ID]/locations/global/dataAgents/[AGENT_ID]
display_name: [AGENT_DISPLAY_NAME]
description: BigQuery Conversational Analytics agent for [DATASET_ID].
labels:
  agent_domain: [DOMAIN_E_G_RETAIL_SALES_SUPPLY_CHAIN]
data_analytics_agent:
  staging_context:
    system_instruction: |
      [INSERT SYSTEM INSTRUCTIONS HERE FOLLOWING THE FORMAT ABOVE]
    glossary_terms:
      - display_name: "[BUSINESS_TERM_OR_KPI]"
        description: "[DEFINITION_OR_FORMULA_E_G_SUM_PROFIT_DIVIDED_BY_SUM_SALES]"
    tables:
      - table:
          name: "[PROJECT_ID].[DATASET_ID].[TABLE_1_NAME]"
          fields:
            - field:
                name: "[COLUMN_NAME]"
                aggregations:
                  - "SUM"
                  - "AVG"
    relationships:
      - relationship:
          name: "[RELATIONSHIP_NAME_E_G_ORDERS_TO_CUSTOMERS]"
          description: "[DESCRIPTION_OF_JOIN]"
          relationship_type: "[one-to-one|one-to-many|many-to-one|many-to-many]"
          join_type: "[inner|outer|left|right|full]"
          left_table: "[PROJECT_ID].[DATASET_ID].[TABLE_1_NAME]"
          right_table: "[PROJECT_ID].[DATASET_ID].[TABLE_2_NAME]"
          relationship_columns:
            - left_column: "[JOIN_COLUMN_1]"
              right_column: "[JOIN_COLUMN_2]"
    additional_descriptions:
      - text: "[ADDITIONAL_GENERAL_INSTRUCTIONS_OR_BUSINESS_RULES]"
    options:
      datasource:
        big_query_max_billed_bytes: '20000000000'
    datasource_references:
      bq:
        table_references:
        - project_id: [PROJECT_ID]
          dataset_id: [DATASET_ID]
          table_id: [TABLE_1_NAME]
        property_graph_references:
        - project_id: [PROJECT_ID]
          dataset_id: [DATASET_ID]
          property_graph_id: [GRAPH_NAME]
          location_boundary: ""
```

### 2. `dump_config.py` Template
```python
import yaml
import os
import requests
import google.auth
from google.auth.transport.requests import Request

def dump_config(project_id, agent_id, location="global", output_file="config.yaml"):
    creds, _ = google.auth.default()
    creds.refresh(Request())
    
    name = f"projects/{project_id}/locations/{location}/dataAgents/{agent_id}"
    url = f"https://geminidataanalytics.googleapis.com/v1beta/{name}"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    
    print(f"Fetching configuration for agent: {name}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        config_dict = response.json()
        
        # Convert camelCase keys to snake_case for consistency with YAML structure
        import re
        def to_snake(d):
            if isinstance(d, dict):
                return {re.sub(r'(?<!^)(?=[A-Z])', '_', k).lower(): to_snake(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [to_snake(i) for i in d]
            return d
            
        snake_config = to_snake(config_dict)
        
        with open(output_file, 'w') as f:
            yaml.dump(snake_config, f, sort_keys=False, indent=2)
        
        print(f"Configuration successfully dumped to {output_file}")
    except Exception as e:
        print(f"Error dumping configuration: {e}")

if __name__ == "__main__":
    PROJECT_ID = "[PROJECT_ID]"
    AGENT_ID = "[AGENT_ID]" # e.g., agent_12345
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "config.yaml")
    
    dump_config(PROJECT_ID, AGENT_ID, output_file=output_path)
```

### 3. `update_config.py` Template
```python
import yaml
import os
import requests
import google.auth
from google.auth.transport.requests import Request

def update_config(yaml_file="config.yaml"):
    if not os.path.exists(yaml_file):
        print(f"File {yaml_file} not found.")
        return

    with open(yaml_file, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    agent_name = config_dict.get('name')
    if not agent_name:
        print("Agent 'name' missing from YAML file.")
        return

    print(f"Updating agent: {agent_name}")

    # Convert snake_case back to camelCase for the REST API
    import re
    def to_camel(d):
        if isinstance(d, dict):
            return {re.sub(r'_([a-z])', lambda m: m.group(1).upper(), k): to_camel(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [to_camel(i) for i in d]
        return d
        
    camel_config = to_camel(config_dict)

    creds, _ = google.auth.default()
    creds.refresh(Request())
    
    url = f"https://geminidataanalytics.googleapis.com/v1beta/{agent_name}?updateMask=displayName,description,labels,dataAnalyticsAgent.stagingContext"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}

    try:
        response = requests.patch(url, headers=headers, json=camel_config)
        response.raise_for_status()
        print("Update succeeded.")
    except Exception as e:
        print(f"Error updating agent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "config.yaml")
    
    update_config(input_path)
```