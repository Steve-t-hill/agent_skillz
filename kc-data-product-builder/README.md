# Knowledge Catalog Data Product Builder Skill

This skill provides expert guidance, Product Manager heuristics, and a dedicated Python CLI tool (`product_manager.py`) for creating, curating, securing, and governing **Knowledge Catalog Data Products** in Google Cloud Dataplex.

> [!WARNING]
> **Data Governance & Co-Location Constraints**:
> * **Location Co-location**: A Data Product and **all** of its bundled assets (BigQuery tables, views, Cloud Storage buckets) must reside in the **exact same Google Cloud region** (e.g., all in `us-central1` or all in `us`).
> * **Asset Deletion Prerequisite**: You must remove all bundled data assets from a Data Product before the product itself can be deleted.
> * **Zombie Permissions**: Deleting a Data Product does not automatically strip underlying IAM permissions previously granted on cross-project data assets.

---

## Key Features

* **Consumption-First Product Design**: Bundles data around business use cases and consumer outcomes rather than organizational ownership.
* **Cross-Domain Asset Packaging**: Unifies disparate BigQuery tables, views, and Cloud Storage buckets spanning different Data Domains into a single consumable package.
* **Persona-Based Access Groups**: Replaces raw infrastructure IAM with abstract consumer roles (e.g., `Financial Analyst`, `Data Scientist`) mapped to Google Groups or user accounts.
* **Built-in Governance Workflows**: Provides end-to-end change request lifecycle management (`request-access`, `list-reviewable-requests`, `approve-request`, `reject-request`).
* **SLA Contracts & Catalog Documentation**: Enriches catalog entries with structured Dataplex aspects, including `refresh-cadence` contracts and `overview` documentation with sample queries.

---

## Common Use Cases

* **Use-Case-Driven Bundling**:
  * Identify tables across domains that answer specific consumer questions and package them into a curated product.
  * **Sample Prompt**:
    > "Analyze our BigQuery tables across the `sales`, `marketing`, and `support` datasets. Bundle the tables needed for 'Customer Churn Insights' into a new Data Product in `us-central1`."
* **Asset Inclusion & Curation**:
  * Add specific BigQuery tables, views, or GCS buckets to a product.
  * **Sample Prompt**:
    > "Add the table `my-gcp-project.crm_data.customer_history` and the view `my-gcp-project.sales_data.v_churn_signals` to the `customer-churn-insights` Data Product."
* **Persona Access Group Configuration**:
  * Set up persona-based access tiers and map them to fine-grained dataset permissions.
  * **Sample Prompt**:
    > "Configure an `analyst` access group mapped to `analysts@example.com` on the `customer-churn-insights` product, and grant `roles/bigquery.dataViewer` on all bundled assets."
* **Self-Service Access Requests & Approvals**:
  * Submit or review consumer change requests for product access.
  * **Sample Prompt**:
    > "List all pending reviewable change requests for Data Products in `us-central1`, and approve request `req-847291`."
* **SLA Contracts & Documentation**:
  * Attach refresh schedules and sample queries to enable self-service consumer onboarding.
  * **Sample Prompt**:
    > "Attach a 'Daily' refresh cadence SLA contract to the `customer-churn-insights` product and document a sample SQL query for high-risk customers."

---

## Installation

To install this skill for Gemini CLI or Antigravity, copy this directory to your skills directory:

```bash
cp -r kc-data-product-builder ~/.agents/skills/
```

### Activate the Skill
Activate the skill within an Antigravity or Gemini session:

```text
activate_skill kc-data-product-builder
```

Once activated, the agent follows the operational playbook in `SKILL.md` and executes tasks via `product_manager.py`.

---

## Authentication

This skill uses **Application Default Credentials (ADC)**. Ensure you have the Google Cloud SDK installed and authenticated locally:

```bash
gcloud auth application-default login
```

Ensure your active identity holds `roles/dataplex.admin` or custom Dataplex Data Product permissions.

---

## CLI Tool: `product_manager.py`

The skill packages `product_manager.py` to communicate directly with the Dataplex REST API (`https://dataplex.googleapis.com/v1`).

### Available Commands Summary

| Category | Command | Description |
| :--- | :--- | :--- |
| **Product CRUD** | `list-products` | List all Data Products in project and location. |
| | `create-product` | Create a new Data Product with owners and approvers. |
| | `get-product` | Get metadata for a specific Data Product. |
| | `update-product` | Update display name, description, owners, or approvers. |
| | `delete-product` | Delete an empty Data Product. |
| **Data Assets** | `list-assets` | List all bundled data assets in a product. |
| | `add-asset` | Add a BigQuery table/view or GCS bucket to a product. |
| | `get-asset` | Retrieve details for a bundled asset. |
| | `remove-asset` | Remove an asset from a Data Product. |
| **Access Groups** | `configure-access-group` | Configure persona access group (Google Group / User). |
| | `set-asset-permissions` | Set IAM roles for an access group on a specific asset. |
| **Governance** | `request-access` | Consumer submits change request for product access. |
| | `list-reviewable-requests` | Approver lists pending change requests. |
| | `list-my-requests` | Consumer lists their submitted change requests. |
| | `get-request` | Get details and status of a change request. |
| | `approve-request` | Approve a pending access change request. |
| | `reject-request` | Reject a pending request with optional comment. |
| **Contracts & Aspects** | `add-refresh-cadence` | Attach `refresh-cadence` SLA contract aspect. |
| | `add-documentation` | Attach `overview` markdown documentation aspect. |

---

## 5-Step Demo: Packaging & Governing a Data Product

### Step 1: Create a Data Product
```bash
python3 product_manager.py create-product \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --product_id="customer-churn-insights" \
  --display_name="Customer Churn Insights" \
  --description="Curated tables and views for detecting and mitigating customer churn risk." \
  --owner_emails="product-owner@example.com" \
  --approver_emails="data-governance-lead@example.com"
```

### Step 2: Bundle Physical Data Assets
Add tables and views across domains into the product:
```bash
python3 product_manager.py add-asset \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --product_id="customer-churn-insights" \
  --asset_id="asset-churn-scores" \
  --resource="//bigquery.googleapis.com/projects/my-gcp-project/datasets/ml_models/tables/churn_scores"
```

### Step 3: Configure Persona Access Groups & Asset Permissions
```bash
# Define analyst access tier
python3 product_manager.py configure-access-group \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --product_id="customer-churn-insights" \
  --group_id="analyst" \
  --display_name="Marketing Analyst Access" \
  --principal_group="mktg-analysts@example.com"

# Grant BigQuery dataViewer on the asset
python3 product_manager.py set-asset-permissions \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --product_id="customer-churn-insights" \
  --asset_id="asset-churn-scores" \
  --group_id="analyst" \
  --iam_roles="roles/bigquery.dataViewer"
```

### Step 4: Attach SLA Contract & Documentation Aspects
```bash
# Attach daily refresh SLA
python3 product_manager.py add-refresh-cadence \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --product_id="customer-churn-insights" \
  --frequency="Daily"

# Attach documentation and sample queries
python3 product_manager.py add-documentation \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --product_id="customer-churn-insights" \
  --content="### High Risk Query Example\n```sql\nSELECT customer_id, score FROM churn_scores WHERE risk = 'HIGH';\n```"
```

### Step 5: Consumer Access Request & Approver Review
```bash
# Consumer requests access
python3 product_manager.py request-access \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --product_id="customer-churn-insights" \
  --access_group_id="analyst" \
  --justification="Need access for Q4 retention campaign optimization."

# Approver lists reviewable requests and approves
python3 product_manager.py list-reviewable-requests \
  --project_id="my-gcp-project" \
  --location="us-central1"

python3 product_manager.py approve-request \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --request_id="req-918273"
```

