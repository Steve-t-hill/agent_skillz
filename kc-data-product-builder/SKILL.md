---
name: kc-data-product-builder
description: >-
  Use this skill to create, manage, bundle, and secure Data Products in Google Cloud Knowledge Catalog.
  Use when the user wants to package related data assets (BigQuery tables, views, GCS buckets) into curated bundles designed to solve specific business use cases or streamline access for consumers.
  Do not use for logical ownership organization (which is handled by Data Domains) or general catalog browsing.
license: Apache-2.0
metadata:
  version: v1
  publisher: Steve Thill
---

# Knowledge Catalog Data Product Builder & Consumption-Oriented Asset Bundling

## TL;DR
This skill provides automated guidance, consumption-first design heuristics, and a dedicated CLI utility (`product_manager.py`) for creating, curating, securing, and governing **Knowledge Catalog Data Products** in Google Cloud. It packages distributed data assets (BigQuery tables, views, GCS buckets) into consumable, business-oriented bundles with persona-based access groups, governance approval workflows, and contract SLAs.

---

## 🧠 Logical Grouping Strategy (Data Product Design)

Unlike **Data Domains** (which group data by **Organizational Ownership** and business architecture), **Data Products** group data by **Consumption and Business Use Cases**. When asked to group assets into a Data Product, you must act as a **Product Manager**.

### 📋 Grouping Heuristics & Decision Criteria

1. **Focus on the Business Outcome (Use Case):**
   * Identify the specific consumer question or capability being targeted (e.g., "Customer Churn Prediction", "Executive Revenue Insights", "Supply Chain Risk Modeling").
   * Bundle *only* the specific assets (tables, views, models) required to satisfy that business outcome. Avoid bundling irrelevant operational tables.
2. **Cross-Domain Packaging:**
   * Assets within a single Data Product can originate from multiple distinct Data Domains (e.g., combining `Billing` data from the Finance domain with `Clickstream` data from the Marketing domain).
   * Your mission is to bridge organizational silos into a unified, consumable package.
3. **Security & Access Abstraction (Access Groups):**
   * Abstract raw infrastructure IAM by creating **Access Groups** representing consumer personas (e.g., `Financial Analyst`, `Data Scientist`, `Marketing Specialist`).
   * Map datasets and tables to appropriate IAM roles (e.g., `roles/bigquery.dataViewer`, `roles/bigquery.admin`) for each group, avoiding manual table-by-table permissions.
4. **Self-Service Enablement (Curation & Contracts):**
   * A true Data Product is more than raw storage; it includes **Context** and **Commitments**.
   * Always attach contracts (e.g., SLA refresh cadence) and rich documentation (e.g., overview, sample queries, metric calculation logic).

### ⚙️ Operational Workflow for Data Product Creation
1. **Identify Use Case & Persona:** Define the business problem, target consumer persona, and access requirements.
2. **Curate Assets:** Select the exact BigQuery tables/views and Cloud Storage resources needed across domains.
3. **Design Access Groups:** Map target personas to Google Groups or user identities and determine their required IAM roles per asset.
4. **Define Contracts & Documentation:** Formulate the SLA refresh frequency (daily, weekly, real-time) and usage guidelines.
5. **Propose & Confirm:** Present the Data Product proposal to the user with full rationale before executing API calls.

---

## 🛠️ Operational Playbook & CLI Tool (`product_manager.py`)

The skill packages a dedicated Python CLI client `product_manager.py` that interacts directly with the Dataplex service endpoint (`https://dataplex.googleapis.com/v1`). The agent invokes this tool via `run_command`.

### Command Reference Summary
* **Product CRUD**: `list-products`, `create-product`, `get-product`, `update-product`, `delete-product`
* **Data Asset Operations**: `list-assets`, `add-asset`, `get-asset`, `remove-asset`
* **Access Groups & Permissions**: `configure-access-group`, `set-asset-permissions`
* **Governance & Approvals**: `request-access`, `list-reviewable-requests`, `list-my-requests`, `get-request`, `approve-request`, `reject-request`
* **Contracts & Catalog Aspects**: `add-refresh-cadence`, `add-documentation`

---

## 📖 Expert Workflows & Recipes

### Recipe 1: End-to-End Use-Case Scaffolding & Product Creation
Use this workflow when the user requests to "create a Data Product for churn prediction" or "bundle these tables into a product."

#### Phase 1: Asset Inspection & Product Design
1. Inspect available tables and views in BigQuery using discovery tools.
2. Formulate the Product definition:
   * **Product ID**: kebab-case identifier (e.g., `customer-churn-insights`).
   * **Display Name**: Clear title (e.g., "Customer Churn Analytics Product").
   * **Description**: Detailed business scope and target questions answered.
   * **Owner Emails**: Product owner email(s).
   * **Approver Emails**: Authorized change request approvers.
3. Present the proposal table to the user and obtain confirmation.

#### Phase 2: Product Provisioning
After approval, create the product:
```bash
python3 product_manager.py create-product \
  --project_id=<project> \
  --location=<location> \
  --product_id=<product-id> \
  --display_name="<Display Name>" \
  --description="<Description>" \
  --owner_emails="<owner@example.com>" \
  --approver_emails="<approver@example.com>"
```

---

### Recipe 2: Bundling Cross-Domain BigQuery and GCS Assets
Include curated physical resources into the Data Product:

```bash
# Add BigQuery Table / View
python3 product_manager.py add-asset \
  --project_id=<project> \
  --location=<location> \
  --product_id=<product-id> \
  --asset_id=<asset-id> \
  --resource="//bigquery.googleapis.com/projects/<project>/datasets/<dataset>/tables/<table>"

# Add GCS Bucket Resource
python3 product_manager.py add-asset \
  --project_id=<project> \
  --location=<location> \
  --product_id=<product-id> \
  --asset_id=<asset-id> \
  --resource="//storage.googleapis.com/projects/_/buckets/<bucket-name>"
```

---

### Recipe 3: Persona Access Group & IAM Role Configuration
Abstract security by binding personas to groups and defining asset-level privileges.

#### Step 1: Configure Access Group on Product
Define an access tier (e.g., `analyst`, `data-scientist`):
```bash
python3 product_manager.py configure-access-group \
  --project_id=<project> \
  --location=<location> \
  --product_id=<product-id> \
  --group_id="analyst" \
  --display_name="Financial Analyst Access" \
  --principal_group="analysts@example.com"
```

#### Step 2: Configure Asset Permissions for Access Group
Grant specific IAM permissions on individual assets for that access group:
```bash
python3 product_manager.py set-asset-permissions \
  --project_id=<project> \
  --location=<location> \
  --product_id=<product-id> \
  --asset_id=<asset-id> \
  --group_id="analyst" \
  --iam_roles="roles/bigquery.dataViewer"
```

---

### Recipe 4: Consumer Access Requests & Approver Governance
Manage the self-service consumer lifecycle with built-in change requests.

#### Consumer Action: Request Product Access
```bash
python3 product_manager.py request-access \
  --project_id=<project> \
  --location=<location> \
  --product_id=<product-id> \
  --access_group_id="analyst" \
  --justification="Need access for Q4 revenue modeling and forecasting."
```

#### Approver Action: Review & Approve / Reject
```bash
# 1. List reviewable pending requests
python3 product_manager.py list-reviewable-requests \
  --project_id=<project> \
  --location=<location>

# 2. Approve Request
python3 product_manager.py approve-request \
  --project_id=<project> \
  --location=<location> \
  --request_id=<change-request-id>

# Or Reject with Feedback
python3 product_manager.py reject-request \
  --project_id=<project> \
  --location=<location> \
  --request_id=<change-request-id> \
  --comment="Please provide a valid project billing code in your justification."
```

---

### Recipe 5: Attaching Contracts (Refresh Cadence) & Documentation Aspects
Enrich the product entry with SLA contracts and rich documentation using Knowledge Catalog aspects.

#### Refresh Cadence Contract:
```bash
python3 product_manager.py add-refresh-cadence \
  --project_id=<project> \
  --location=<location> \
  --product_id=<product-id> \
  --frequency="Daily"
```
*(Options: `Hourly`, `Daily`, `Weekly`, `Monthly`, `Real-time`)*

#### Overview Documentation & Sample Queries:
```bash
python3 product_manager.py add-documentation \
  --project_id=<project> \
  --location=<location> \
  --product_id=<product-id> \
  --content="### Overview\nThis product provides churn risk scores.\n\n### Sample Query\n```sql\nSELECT * FROM churn_scores WHERE risk_tier = 'HIGH';\n```"
```

---

### Recipe 6: Safe Teardown & Cascading Asset Unbundling
Dataplex requires that all bundled assets must be deleted before a Data Product can be deleted.

#### Decommission Sequence:
1. **List all assets**:
   ```bash
   python3 product_manager.py list-assets --project_id=<project> --location=<location> --product_id=<product-id>
   ```
2. **Remove each asset**:
   ```bash
   python3 product_manager.py remove-asset --project_id=<project> --location=<location> --product_id=<product-id> --asset_id=<asset-id>
   ```
3. **Delete empty product**:
   ```bash
   python3 product_manager.py delete-product --project_id=<project> --location=<location> --product_id=<product-id>
   ```

---

## ⚠️ Edge Cases & Governance Constraints

1. **Location Co-location**: A Data Product and **all** of its bundled assets must reside in the exact same Google Cloud region (e.g., both in `us-central1` or both in `us`).
2. **Limits on Asset Counts**: Maximum 10 assets can be added per individual request; hard cap of **50 assets** total per Data Product.
3. **Zombie Permissions**: Deleting a Data Product does not automatically revoke cross-project IAM permissions previously granted on underlying storage resources.
4. **Empty Product Prerequisite for Deletion**: Attempting to delete a Data Product that still contains data assets will fail with an HTTP 400/409 error.
5. **No Zonal Buckets**: Cloud Storage zonal buckets are not supported as data assets.

---

## 🔑 Authentication & Prerequisites
The CLI tool uses Application Default Credentials (ADC):
```bash
gcloud auth application-default login
```
Ensure your active identity holds appropriate roles:
* `roles/dataplex.admin` or custom Data Product manager role.
* `roles/bigquery.admin` or dataset IAM permissions for asset-level access configuration.

