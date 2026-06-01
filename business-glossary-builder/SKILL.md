---
name: business-glossary-builder
description: |
  Expert guidance and automated agent protocol for managing Google Cloud Knowledge Catalog Business Glossaries.
  This skill provides the ability to create, update, and manage glossaries, categories, and terms, as well as link terms to data assets and columns.
  It enforces a strict "Exhaustive Analysis" rule to ensure 100% conceptual coverage of BigQuery datasets in a single pass.
  Use this skill when:
    1. Building a new business glossary from scratch for a BigQuery dataset.
    2. Auditing existing glossaries for missing terms or technical mappings.
    3. Establishing data stewardship and ownership metadata across a business ontology.
    4. Linking related or synonymous business concepts to improve discoverability.
license: Apache-2.0
metadata:
  version: v2
  publisher: Steve Thill
---

# Knowledge Catalog Business Glossary & Automated Ontology Mapping

## TL;DR
This skill provides automated guidance and a CLI tool (`glossary_manager.py`) for managing Knowledge Catalog Business Glossaries. It allows you to programmatically build out a business ontology and map it to your physical data assets in BigQuery and beyond.

---

## Core Governance Principles

When creating or managing a business glossary, always adhere to these industry-standard data governance principles:

1. **Business-First Approach**: A business glossary is *not* a technical data dictionary. It standardizes the naming and meaning of business concepts. Standardize names to clear Business Title Case (e.g., "Customer ID", "Sale Price") instead of technical column names.
2. **Avoid Column Duplication**: Do not simply create a term for every single column. Identify the conceptual term.
   * *Example*: Column names such as `customers.id`, `events.USER_ID`, and `order_items.USER_ID` all map to a single business term: "Customer ID".
3. **Comprehensive Column-Level Mapping**: Map defined business terms to all of their physical column implementations across BigQuery datasets. Ensure that **every column in every table** is analyzed to represent all relevant business terms.
4. **Rule of Exhaustive Analysis**: When asked to build a glossary for a dataset, DO NOT perform a partial analysis. You must retrieve the schema for every table in the dataset and identify all conceptual terms before presenting a proposal to the user.
5. **Rich & Actionable Metadata**: Go beyond simple descriptions. Ensure all items include:
   * **Overview**: Calculation logic/formulas (e.g., how "Total Revenue" is calculated) and Related KPIs (how this term affects key business indicators like "Directly impacts Gross Margin").
   * **Ownership**: A proposed Data Steward or Subject Matter Expert (SME).
6. **Strict ID Conventions**: Glossary, Category, and Term IDs must contain **only lowercase letters, numbers, and/or hyphens** (e.g., `customer-id`, `sales-data`). Convert display labels to lowercase with hyphens.

---

## CLI Tool: `glossary_manager.py`
The skill includes a Python script `glossary_manager.py` that handles all REST API interactions with the Knowledge Catalog. The agent invokes this tool using the `run_command` tool.

### Command Reference Summary
* **Glossary**: `list-glossaries`, `create-glossary`, `get-glossary`, `add-glossary-overview`
* **Category**: `list-categories`, `create-category`, `add-category-overview`, `add-category-contacts`
* **Term**: `list-terms`, `create-term`, `add-term-overview`, `add-term-contacts`
* **Linking**: `attach-term-to-data-asset`, `attach-term-to-column`, `create-synonym-link`, `create-related-link`

---

## Expert Workflows & Recipes

### Recipe 1: End-to-End Comprehensive Glossary Discovery, Scaffolding, & Population
Use this workflow when the user requests to "create a glossary for my BigQuery dataset" or "build a glossary from scratch."

#### Phase 1: Exhaustive Asset & Schema Discovery
1. **Inspect Full Dataset Schema**: Use BigQuery tools (such as `datacloud_bigquery_remote`) to list **all** tables and get **every** schema.
2. **Exhaustive Domain Mapping (Categories)**: Analyze every table name and description to group the entire dataset into core business domains (e.g., Customer, Sales, Inventory, Logistics).
3. **Exhaustive Business Term Identification**: Walk through **every column of every table** to extract conceptual terms. Ensure 100% conceptual coverage of the physical schema. Do not leave any relevant column unmapped.

#### Phase 2: Enrich & Map
1. **Define Attributes**: Draft short, clear definitions for each term.
2. **Create Overviews**: Write detailed business-focused overviews, including:
   * **Calculation Logic**: Formula or derivation.
   * **Related KPIs**: e.g., "Directly affects Monthly Active Users (MAU)."
3. **Technical Mapping**: Document the source-to-target mappings, linking the business term to all of its physical column paths (e.g. `project.dataset.table.column`).

#### Phase 3: Review & Scaffolding
Present the proposed structure in two parts to the user for validation before making any API calls:
1. A table of the enriched **Business Terms**.
2. A mapping list showing each term and all the technical assets it maps to.

#### Phase 4: Implementation Commands
After approval, run the following sequence:
1. **Create Glossary**:
   ```bash
   python3 glossary_manager.py create-glossary --project_id=<project> --location=<location> --glossary_id=<glossary-id> --display_name="<Name>" --description="<Desc>"
   ```
2. **Add Glossary Overview**:
   ```bash
   python3 glossary_manager.py add-glossary-overview --project_id=<project> --location=<location> --glossary_id=<glossary-id> --overview="<Detailed Overview>"
   ```
3. **Create Categories & Overviews**:
   ```bash
   python3 glossary_manager.py create-category --project_id=<project> --location=<location> --glossary_id=<glossary-id> --category_id=<category-id> --display_name="<Category Name>" --description="<Desc>"
   python3 glossary_manager.py add-category-overview --project_id=<project> --location=<location> --glossary_id=<glossary-id> --category_id=<category-id> --overview="<Overview>"
   ```
4. **Create Terms & Overviews**:
   ```bash
   # Nesting inside a Category:
   python3 glossary_manager.py create-term --project_id=<project> --location=<location> --glossary_id=<glossary-id> --term_id=<term-id> --display_name="<Term Name>" --description="<Desc>" --parent_category_id=<category-id>
   # Add Term Overview:
   python3 glossary_manager.py add-term-overview --project_id=<project> --location=<location> --glossary_id=<glossary-id> --term_id=<term-id> --overview="<Overview Details>"
   ```
5. **Attach Term to Column (Lineage Mapping)**:
   ```bash
   python3 glossary_manager.py attach-term-to-column --project_id=<src-project> --entry_location_id=<src-dataset-location> --entry_dataset_name=<src-dataset> --entry_table_name=<src-table> --entry_column_name=<src-col> --term_project_id=<glossary-project> --term_location_id=<glossary-location> --term_glossary_id=<glossary-id> --term_id=<term-id> --entry_link_id=<unique-link-id>
   ```

---

### Recipe 2: Semantic Relationship & Synonym Audit
Use this workflow when the user requests to "find synonyms" or "link related terms."

1. **List Existing Terms**: Retrieve all terms in the glossary using `list-terms`.
2. **Perform Semantic Analysis**: Review the names, descriptions, and contexts to identify:
   * **Synonyms**: Identical or near-identical concepts (e.g., "Client" and "Customer").
   * **Related Terms**: Conceptually connected but distinct terms (e.g., "Order" and "Product", "Customer" and "Order").
3. **Apply Linkages**:
   * **Synonym Link**:
     ```bash
     python3 glossary_manager.py create-synonym-link --term1_project_id=<proj> --term1_location=<loc> --term1_glossary_id=<glossary> --term1_id=<term-a> --term2_project_id=<proj> --term2_location=<loc> --term2_glossary_id=<glossary> --term2_id=<term-b> --entry_link_id=<unique-synonym-link-id>
     ```
   * **Related Link**:
     ```bash
     python3 glossary_manager.py create-related-link --term1_project_id=<proj> --term1_location=<loc> --term1_glossary_id=<glossary> --term1_id=<term-a> --term2_project_id=<proj> --term2_location=<loc> --term2_glossary_id=<glossary> --term2_id=<term-b> --entry_link_id=<unique-related-link-id>
     ```

---

### Recipe 3: Bulk Import from CSV
Use this workflow when the user requests to "import business terms from a CSV file."

1. **Read CSV Content**: Parse the CSV using file-reading tools.
2. **Validate Structure**: Ensure columns `label` and `description` are present.
3. **Generate ID & Format**:
   * Convert `label` to lowercase and replace spaces/special characters with a hyphen (`-`) to generate a valid `term_id` (e.g. "Access Control Policy" -> "access-control-policy").
4. **Execute Creation Batch**: Iteratively invoke `create-term` for each row. If a parent category is provided, include `--parent_category_id`.

---

### Recipe 4: Ownership & Stewardship Assignment
Use this workflow when the user requests to "assign a steward/SME" or "batch update contacts."

1. **Identify Scope**: Find target categories or terms belonging to the designated business domain.
2. **Retrieve Details**: Ensure you have the steward's `name` and `email` (used as identity ID).
3. **Assign Stewards**:
   * **For Category**:
     ```bash
     python3 glossary_manager.py add-category-contacts --project_id=<project> --location=<location> --glossary_id=<glossary-id> --category_id=<category-id> --contact_name="<Steward Name>" --contact_email="<Steward Email>"
     ```
   * **For Term**:
     ```bash
     python3 glossary_manager.py add-term-contacts --project_id=<project> --location=<location> --glossary_id=<glossary-id> --term_id=<term-id> --contact_name="<Steward Name>" --contact_email="<Steward Email>"
     ```

---

## Authentication
The script uses Application Default Credentials (ADC). Ensure you have authenticated locally using:
```bash
gcloud auth application-default login
```
