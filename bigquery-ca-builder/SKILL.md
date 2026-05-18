# BigQuery Conversational Analytics (BQCA) Agent Builder

## TL;DR
This skill guides the agent in automatically generating configuration and deployment files for a BigQuery Conversational Analytics (BQCA) Agent using the `geminidataanalytics_v1beta` API. 

Use this skill when a user asks to "build a conversational analytics agent", "create a BQCA agent", or "generate a config.yaml for an NL2SQL agent" against an existing BigQuery dataset or Property Graph.

## The Output Artifacts
When invoked, the agent MUST generate a directory (e.g., `bqca_[name]_agent`) containing the following 4 files:

1.  **`README.md`**: Documentation explaining the agent's purpose, the required Python packages (`google-cloud-geminidataanalytics`, `pyyaml`), and instructions on using the Python scripts.
2.  **`config.yaml`**: The declarative configuration defining the agent's identity, system instructions (persona, context, rules, examples), and the dataset schema references.
3.  **`dump_config.py`**: A Python script to download the live config to `config.yaml`.
4.  **`update_config.py`**: A Python script to push the local `config.yaml` to GCP.

## System Instructions (The Heart of `config.yaml`)
The `system_instruction` block inside `config.yaml` (specifically within `data_analytics_agent.staging_context`) must follow this exact structured markdown format:

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
    options:
      datasource:
        big_query_max_billed_bytes: '20000000000'
    datasource_references:
      bq:
        table_references:
        - project_id: [PROJECT_ID]
          dataset_id: [DATASET_ID]
          table_id: [TABLE_1_NAME]
        - project_id: [PROJECT_ID]
          dataset_id: [DATASET_ID]
          table_id: [TABLE_2_NAME]
```

### 2. `dump_config.py` Template
```python
import yaml
import os
from google.cloud import geminidataanalytics_v1beta as geminidataanalytics

def dump_config(project_id, agent_id, location="global", output_file="config.yaml"):
    client = geminidataanalytics.DataAgentServiceClient()
    name = f"projects/{project_id}/locations/{location}/dataAgents/{agent_id}"
    
    print(f"Fetching configuration for agent: {name}")
    request = geminidataanalytics.GetDataAgentRequest(name=name)
    
    try:
        response = client.get_data_agent(request=request)
        config_dict = geminidataanalytics.DataAgent.to_dict(response)
        
        with open(output_file, 'w') as f:
            yaml.dump(config_dict, f, sort_keys=False, indent=2)
        
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
import time
from google.cloud import geminidataanalytics_v1beta as geminidataanalytics
from google.protobuf import field_mask_pb2

def update_config(yaml_file="config.yaml"):
    client = geminidataanalytics.DataAgentServiceClient()
    
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

    agent_proto = geminidataanalytics.DataAgent.from_json(yaml.dump(config_dict))
    
    paths = [
        "display_name",
        "description",
        "labels",
        "data_analytics_agent.staging_context"
    ]
    
    update_mask = field_mask_pb2.FieldMask(paths=paths)
    
    request = geminidataanalytics.UpdateDataAgentRequest(
        data_agent=agent_proto,
        update_mask=update_mask,
    )

    try:
        operation = client.update_data_agent(request=request)
        print("Update in progress...")
        
        while not operation.done():
            time.sleep(2)
            print("...")

        if operation.exception():
            print("Operation failed:", operation.exception())
        else:
            print("Operation succeeded.")
    except Exception as e:
        print(f"Error updating agent: {e}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "config.yaml")
    
    update_config(input_path)
```