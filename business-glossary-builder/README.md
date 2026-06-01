# Knowledge Catalog Business Glossary Builder Skill

This skill provides expert guidance, automated workflows, and a specialized Python CLI tool (`glossary_manager.py`) for building and managing Google Cloud Knowledge Catalog Business Glossaries. It helps you programmatically define a business ontology and map it directly to physical data assets in BigQuery.

> [!WARNING]
> **Data Loss & Irreversible Operations**: This skill performs CRUD (Create, Read, Update, Delete) operations directly against the Google Cloud Knowledge Catalog Business Glossary. Incorrect commands or automation logic may result in irreversible data loss, metadata overwrites, or broken lineage links. Always verify your target project, location, and glossary IDs before execution.

---

## Key Features
* **Complete Lifecycle**: Create and manage glossaries, categories, and terms.
* **Rich Metadata**: Add business overviews and assign data stewards/SMEs.
* **Semantic Linking**: Create synonym links and related-term links between items.
* **Technical Asset Mapping**: Link terms directly to BigQuery datasets, tables, and columns.
* **Bulk Import**: Import terms from CSV files with automatic formatting and ID generation.

---

## Common Use Cases

* **Cold Start Scaffolding**: Bootstrap a new business glossary by extracting schema metadata from physical technical assets (like BigQuery tables) and auto-generating initial categories and terms based on technical descriptions and naming patterns.
  * **Sample Prompt**:
    > "Analyze the dataset `my-project.retail_data` and bootstrap a new business glossary `retail-glossary` in `global`. Extract all table structures, infer the conceptual business categories/terms, and generate a rich scaffolding mapped to the physical column schema."
* **Automated Glossary Import**: Import legacy or pre-existing business terms from diverse external formats (such as CSV or Markdown) and programmatically create and link them into the business glossary `retail-glossary` in global.
  * **Sample Prompt**:
    > "I have a CSV file at `./raw_terms.csv` containing columns for term name, definition, and steward. Please parse this file and programmatically create all matching terms inside the existing `retail-glossary` glossary in `global`."
* **Bulk Metadata Operations**: Perform bulk operations against large business catalogs, such as mass-assigning data stewards, aligning contact emails, or establishing bulk related-term linkages in a single run.
  * **Sample Prompt**:
    > "Assign `data-governance-team@company.com` as the data steward for all terms under the 'Finance' category in the `retail-glossary` in `global`."
* **Governance Gap & Audit Scanning**: Programmatically scan BigQuery datasets to identify undocumented fields or columns that lack business terms, and find terms missing required stewards or definitions.
  * **Sample Prompt**:
    > "Scan our `my-project.retail_data` dataset in BigQuery and compare it against the `retail-glossary` in `global`. Generate a report listing all columns that do not have an attached glossary term, and identify any terms that are missing a description or a designated data steward."
* **Multi-Glossary Consolidation**: Reconcile and merge separate glossaries from different departments or legacy systems, programmatically identifying synonym relationships and mapping shared definitions.
  * **Sample Prompt**:
    > "We have two distinct glossaries: `retail-sales-glossary` and `online-sales-glossary`. Analyze both to identify overlapping concepts, create synonym links for matches (like 'client' and 'purchaser'), and generate a consolidation proposal to merge them into a single enterprise glossary."


---

## Installation

To install this skill, copy this directory to your global agents skills folder:

```bash
cp -r business-glossary-builder ~/.agents/skills/
```

### Activate the Skill
Activate the skill within an Antigravity or Antigravity CLI session:

```text
activate_skill business-glossary-builder
```

Once activated, the agent gains access to the expert workflows documented in `SKILL.md` and can invoke `glossary_manager.py` via command-line tools.

---

## Authentication

This skill uses **Application Default Credentials (ADC)**. Ensure you have the Google Cloud SDK installed and are authenticated locally:

```bash
gcloud auth application-default login
```

Ensure your active Google Cloud identity has sufficient IAM permissions (e.g., Dataplex Administrator, BigQuery Admin, or custom roles for managing entry groups and links).

---

## CLI Tool: `glossary_manager.py`

The skill packages a lightweight Python CLI client to execute operations against the Dataplex REST API.

### Available Commands
* **Glossary Management**: `list-glossaries`, `create-glossary`, `get-glossary`, `add-glossary-overview`
* **Category Management**: `list-categories`, `create-category`, `add-category-overview`, `add-category-contacts`
* **Term Management**: `list-terms`, `create-term`, `add-term-overview`, `add-term-contacts`
* **Relationship & Lineage Mapping**: `attach-term-to-data-asset`, `attach-term-to-column`, `create-synonym-link`, `create-related-link`

### CLI Syntax Example
```bash
python3 glossary_manager.py create-glossary \
  --project_id="your-project-id" \
  --location="us-central1" \
  --glossary_id="core-glossary" \
  --display_name="Core Business Glossary" \
  --description="Standard business ontology definitions."
```

## Powerful Integrations: BigQuery MCP Server

This skill is designed to work seamlessly with BigQuery MCP servers (such as `bigquery` or `datacloud_bigquery_remote`). These servers provide the agent with the necessary tools to:
* **Discover Assets**: List all tables and datasets in a project.
* **Inspect Schemas**: Programmatically retrieve column names, types, and descriptions.
* **Semantic Analysis**: Examine sample data or detailed table metadata to infer business meaning.

Using a BigQuery MCP server (whether connecting to local data or remote Google Cloud projects) is **highly recommended** for Step 1, as it enables the "Exhaustive Glossary Scaffolding" workflow.

---

## 4-Step Demo: Building a Business Glossary

The following workflow demonstrates how to build, populate, enrich, and assign ownership to a business glossary. You can ask the agent to perform these steps, or run the CLI commands manually.

### Step 1: Exhaustive Glossary Scaffolding
Analyze the **entire** BigQuery dataset schema across all tables and columns. Identify all core business domains, infer every relevant conceptual business term, create the glossary structure, and map every technical column to its business definition in a single pass.
```text
"Please create and populate a new business glossary named 'ecom-glossary' in the 'us-central1' location. Perform an exhaustive analysis of the 'my-gcp-project.ecommerce' dataset in region 'us', ensuring every single column in every table is mapped to a Business Term or Category."
```

### Step 2: Identify and Link Related Terms
Identify conceptual, non-synonymous relationships between terms (e.g., linking "Order" to "Customer" and "Product").
```text
"In the glossary 'ecom-glossary' in project 'my-gcp-project' at location 'us-central1', please identify and link related terms."
```
*Equivalent CLI Command:*
```bash
python3 glossary_manager.py create-related-link \
  --term1_project_id="my-gcp-project" --term1_location="us-central1" --term1_glossary_id="ecom-glossary" --term1_id="order" \
  --term2_project_id="my-gcp-project" --term2_location="us-central1" --term2_glossary_id="ecom-glossary" --term2_id="customer" \
  --entry_link_id="order-customer-related-link"
```

### Step 3: Identify and Link Synonyms
Create synonym links between terms with near-identical meanings (e.g., linking "Client" and "Customer").
```text
"In the glossary 'ecom-glossary' in project 'my-gcp-project' at location 'us-central1', please identify and link synonymous terms."
```
*Equivalent CLI Command:*
```bash
python3 glossary_manager.py create-synonym-link \
  --term1_project_id="my-gcp-project" --term1_location="us-central1" --term1_glossary_id="ecom-glossary" --term1_id="customer" \
  --term2_project_id="my-gcp-project" --term2_location="us-central1" --term2_glossary_id="ecom-glossary" --term2_id="client" \
  --entry_link_id="customer-client-synonym-link"
```

### Step 4: Assign Data Stewards & Contacts
Establish data governance ownership by attaching data steward contacts to all terms and categories in the glossary.
```text
"Add the contact Jane Doe (jane.doe@example.com) to each category and term in my-gcp-project ecom-glossary in us-central1."
```
*Equivalent CLI Command:*
```bash
python3 glossary_manager.py add-term-contacts \
  --project_id="my-gcp-project" --location="us-central1" --glossary_id="ecom-glossary" --term_id="customer" \
  --contact_name="Jane Doe" --contact_email="jane.doe@example.com"
```
