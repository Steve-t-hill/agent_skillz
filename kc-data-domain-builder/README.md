# Knowledge Catalog Data Domain Builder Skill

This skill provides expert guidance, Domain-Driven Design (DDD) heuristics, and a dedicated Python CLI tool (`domain_manager.py`) for creating, organizing, authorizing, and managing Google Cloud Knowledge Catalog / Dataplex Data Domains and Subdomains.

> [!WARNING]
> **Data Governance & Binding Considerations**: This skill performs CRUD (Create, Read, Update, Delete) operations and IAM policy bindings directly against the Dataplex and BigQuery APIs.
> * A physical resource URI (e.g., BigQuery dataset or individual table) can only belong to **one** data domain.
> * If individual tables within a single dataset belong to different subdomains, bind each table directly to its subdomain rather than binding the entire dataset to a parent domain.
> * A domain can only be deleted once **all child subdomains and resource bindings are deleted**.
> * Always verify target project IDs, locations, and domain hierarchies before executing changes.

---

## Key Features

* **Domain-Driven Design (DDD) Scaffolding**: Automatically groups physical datasets and tables into Source-Oriented or Consumer-Oriented bounded contexts.
* **Concise Plain-Text Descriptions & Rich Markdown Overviews**: Maintains clean, 1–2 sentence plain-text descriptions on domain resources while attaching rich Markdown documentation via Knowledge Catalog's native Overview aspects (`contentType: "MARKDOWN"`).
* **Granular Table-Level Subdomain Mapping**: Maps and binds individual BigQuery tables directly to subdomains, enabling clean governance across shared or monolithic datasets without moving or copying physical data.
* **Hierarchical Subdomains**: Supports multi-level business domains (up to 5 nesting levels and 50 subdomains per domain).
* **3-Step Resource Inclusion Workflow**: Automates retrieving the domain's service agent principal (`policyMember`), authorizing target BigQuery datasets or individual tables, and creating resource bindings.
* **IAM & Role Management**: Manages domain-level policies (`dataDomainAdmin`, `dataDomainEditor`, `dataDomainViewer`, `dataDomainEntryReader`).
* **Scoped Semantic Search**: Restricts Knowledge Catalog discovery queries to specific domain contexts.
* **Safe Cascading Teardown**: Systematically unbinds resources and deletes subdomains to allow clean domain decommission.

---

## Common Use Cases

* **Cold Start Domain Design**:
  * Analyze an entire GCP project's datasets and tables, infer business boundaries, and propose a clean domain/subdomain architecture with table-level mappings.
  * **Sample Prompt**:
    > "Analyze all datasets and tables in project `my-gcp-project` and group them into logical domains and subdomains using Domain-Driven Design principles. Propose the hierarchy before creating anything."
* **Granular Table-to-Subdomain Binding**:
  * Bind specific tables within a shared dataset to distinct subdomains.
  * **Sample Prompt**:
    > "Under the `ecommerce` domain in `us-central1`, bind tables `orders` and `order_items` to subdomain `order-management`, and table `inventory` to subdomain `inventory-management`."
* **Resource Binding & Authorization**:
  * Authorize and bind BigQuery datasets or tables to a domain.
  * **Sample Prompt**:
    > "Bind dataset `my-gcp-project.finance_ledger` to the `finance-core` domain in location `us-central1`. Handle the domain principal permissions automatically."
* **Multi-Tier Subdomain Scaffolding**:
  * Build nested subdomains under a core department domain.
  * **Sample Prompt**:
    > "Under the `supply-chain` domain in `us-central1`, create two subdomains: `procurement` and `warehouse-logistics`, assigning `logistics-lead@example.com` as the owner."
* **Domain Access Governance**:
  * Grant viewer or reader roles on a domain to specific teams or groups.
  * **Sample Prompt**:
    > "Grant `roles/dataplex.dataDomainViewer` on the `marketing-analytics` domain in `us-central1` to `group:mktg-analysts@example.com`."
* **Scoped Catalog Search**:
  * Search Knowledge Catalog entries strictly within a domain's boundary.
  * **Sample Prompt**:
    > "Search for tables related to 'churn prediction' strictly within the `customer-science` domain in `us-central1`."

---

## Installation

To install this skill for Gemini CLI or Antigravity, copy this directory to your skills directory:

```bash
cp -r kc-data-domain-builder ~/.agents/skills/
```

### Activate the Skill
Activate the skill within an Antigravity or Gemini session:

```text
activate_skill kc-data-domain-builder
```

Once activated, the agent can follow the operational playbook in `SKILL.md` and execute commands via `domain_manager.py`.

---

## Authentication

This skill uses **Application Default Credentials (ADC)**. Ensure you have the Google Cloud SDK installed and authenticated locally:

```bash
gcloud auth application-default login
```

Ensure your active Google Cloud identity holds `roles/dataplex.dataDomainAdmin` or `roles/dataplex.admin` on the target project and location.

---

## CLI Tool: `domain_manager.py`

The skill packages `domain_manager.py` to communicate directly with the Dataplex REST API (`https://dataplex.googleapis.com/v1`) and BigQuery IAM APIs.

### Available Commands Summary

| Category | Command | Description |
| :--- | :--- | :--- |
| **Domain CRUD** | `list-domains` | List all domains in project and location. |
| | `create-domain` | Create a top-level data domain. |
| | `create-subdomain` | Create a nested subdomain under a parent domain. |
| | `get-domain` | Retrieve domain metadata and `policyMember`. |
| | `list-subdomains` | List subdomains of a parent domain. |
| | `update-domain` | Update description, display name, or labels. |
| | `delete-domain` | Delete an empty domain (no bindings or subdomains). |
| **IAM Control** | `get-iam-policy` | Fetch IAM access control policy for a domain. |
| | `set-iam-policy` | Set or replace domain IAM policy from JSON. |
| | `add-iam-member` | Add role binding for a user/group/service account. |
| **Resource Binding** | `get-domain-principal` | Extract the domain's `policyMember` IAM identity. |
| | `authorize-dataset` | Grant domain principal metadata viewer on BigQuery dataset. |
| | `authorize-table` | Grant domain principal metadata viewer directly on BigQuery table. |
| | `bind-resource` | Bind BigQuery dataset, table, or project resource URI to domain. |
| | `list-bindings` | List all resources included in the domain. |
| | `unbind-resource` | Remove resource from domain by binding ID. |
| **Search** | `search-entries` | Execute scoped semantic search within domain context. |
| **Overview Docs** | `set-overview` | Set native Knowledge Catalog Overview aspect content (Markdown/HTML). |
| | `get-overview` | Retrieve native Knowledge Catalog Overview aspect content. |

---

## 5-Step Demo: Granular Table-Level Subdomain Mapping & Overviews

### Step 1: Create Parent Domain and Subdomains
```bash
# Parent Domain
python3 domain_manager.py create-domain \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --domain_id="retail-enterprise" \
  --display_name="Retail Enterprise Domain" \
  --description="Enterprise domain covering customer engagement, commerce, and merchandising." \
  --contact_name="Alice Smith" \
  --contact_role="owner" \
  --contact_email="alice.smith@example.com"

# Subdomain
python3 domain_manager.py create-subdomain \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --domain_id="customer-experience" \
  --parent_domain_id="retail-enterprise" \
  --display_name="Customer Experience & Engagement" \
  --description="Governs customer profiles, interactions, and support history."
```

### Step 2: Retrieve Subdomain Principal (Step A)
```bash
python3 domain_manager.py get-domain-principal \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --domain_id="customer-experience"
```
*Sample Output:*
```json
{
  "status": "ok",
  "principal": "principal://dataplex.googleapis.com/projects/123456789/name/locations/us-central1/dataDomains/customer-experience",
  "domain_id": "customer-experience"
}
```

### Step 3: Authorize & Bind Individual Table (Steps B & C)
```bash
# Step B: Authorize principal directly on the target BigQuery table
python3 domain_manager.py authorize-table \
  --project_id="my-gcp-project" \
  --dataset_id="shared_retail" \
  --table_id="customers" \
  --principal="principal://dataplex.googleapis.com/projects/123456789/name/locations/us-central1/dataDomains/customer-experience" \
  --role="roles/bigquery.metadataViewer"

# Step C: Bind the table resource URI to the subdomain
python3 domain_manager.py bind-resource \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --domain_id="customer-experience" \
  --binding_id="customers-table-binding" \
  --resource="//bigquery.googleapis.com/projects/my-gcp-project/datasets/shared_retail/tables/customers"
```

### Step 4: Populate Native Knowledge Catalog Overview Aspect
Enrich the domain documentation in the Google Cloud Console:
```bash
python3 domain_manager.py set-overview \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --domain_id="customer-experience" \
  --content="# Customer Experience Overview\n\nGoverns customer lifecycle data, clickstream, and contact center interactions." \
  --content_type=MARKDOWN
```

### Step 5: Scoped Semantic Search within Domain
Discover entries constrained to this subdomain:
```bash
python3 domain_manager.py search-entries \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --domain_id="customer-experience" \
  --query="customer contact information" \
  --semantic_search=true \
  --page_size=25
```
