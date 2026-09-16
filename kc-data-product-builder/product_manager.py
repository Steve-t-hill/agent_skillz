#  Copyright 2025-2026 Steve Thill
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Knowledge Catalog Data Product Manager CLI and Library.

Provides a unified interface for creating, managing, bundling, securing, and
governing Dataplex Data Products via the Dataplex REST API v1.
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional
import google.auth
from google.auth.transport.requests import Request
import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("product_manager")

DATAPLEX_API_BASE = "https://dataplex.googleapis.com/v1"
CRM_API_BASE = "https://cloudresourcemanager.googleapis.com/v1"


def get_credentials() -> google.auth.credentials.Credentials:
    """Retrieves and refreshes Application Default Credentials.

    Returns:
        Valid Google Auth credentials.

    Raises:
        google.auth.exceptions.DefaultCredentialsError: If credentials cannot
            be located.
    """
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds


def get_auth_headers() -> Dict[str, str]:
    """Generates authorization headers with a valid Bearer token.

    Returns:
        Dictionary containing Authorization and Content-Type headers.
    """
    creds = get_credentials()
    return {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }


def get_project_number(project_id: str) -> str:
    """Resolves numerical project number from project ID.

    If project_id is already numeric, it returns it directly. Otherwise, it
    queries the Cloud Resource Manager API.

    Args:
        project_id: The GCP project ID or project number.

    Returns:
        The numerical project number as a string.
    """
    if project_id.isdigit():
        return project_id

    url = f"{CRM_API_BASE}/projects/{project_id}"
    headers = get_auth_headers()
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return str(data.get("projectNumber"))


# ==============================================================================
# 1. Core Data Product CRUD Operations
# ==============================================================================


def list_products(
    project_id: str,
    location: str,
    page_size: int = 50,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Lists all Data Products in a given project and location.

    Args:
        project_id: GCP project ID.
        location: Region identifier (e.g., 'us-central1').
        page_size: Maximum number of products to return.
        page_token: Pagination token.

    Returns:
        Dictionary containing status and list of data products.
    """
    url = f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/dataProducts"
    headers = get_auth_headers()
    params: Dict[str, Any] = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def create_product(
    project_id: str,
    location: str,
    product_id: str,
    display_name: str,
    description: str,
    owner_emails: Optional[List[str]] = None,
    approver_emails: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Creates a new Data Product.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique kebab-case identifier for the product.
        display_name: Human-readable title.
        description: Detailed summary of use cases and business outcome.
        owner_emails: List of owner email addresses.
        approver_emails: List of authorized change request approver emails.

    Returns:
        Dictionary containing created product details or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts?data_product_id={product_id}"
    )
    headers = get_auth_headers()
    payload: Dict[str, Any] = {
        "display_name": display_name,
        "description": description,
    }

    if owner_emails:
        payload["owner_emails"] = owner_emails

    if approver_emails:
        payload["access_approval_config"] = {
            "approver_emails": approver_emails
        }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def get_product(
    project_id: str,
    location: str,
    product_id: str
) -> Dict[str, Any]:
    """Retrieves details of a Data Product.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.

    Returns:
        Dictionary containing product metadata or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}"
    )
    headers = get_auth_headers()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def update_product(
    project_id: str,
    location: str,
    product_id: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    owner_emails: Optional[List[str]] = None,
    approver_emails: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Updates mutable fields of a Data Product.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.
        display_name: New display name.
        description: New description.
        owner_emails: New list of owner emails.
        approver_emails: New list of approver emails.

    Returns:
        Dictionary containing updated product or error.
    """
    update_masks: List[str] = []
    payload: Dict[str, Any] = {}

    if display_name is not None:
        payload["display_name"] = display_name
        update_masks.append("display_name")
    if description is not None:
        payload["description"] = description
        update_masks.append("description")
    if owner_emails is not None:
        payload["owner_emails"] = owner_emails
        update_masks.append("owner_emails")
    if approver_emails is not None:
        payload["access_approval_config"] = {
            "approver_emails": approver_emails
        }
        update_masks.append("access_approval_config.approver_emails")

    if not update_masks:
        return {"status": "error", "message": "No update fields specified."}

    mask_str = ",".join(update_masks)
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}?update_mask={mask_str}"
    )
    headers = get_auth_headers()

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def delete_product(
    project_id: str,
    location: str,
    product_id: str
) -> Dict[str, Any]:
    """Deletes an empty Data Product.

    All data assets must be removed before deleting the product.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.

    Returns:
        Dictionary with status ok or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}"
    )
    headers = get_auth_headers()
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return {"status": "ok", "message": f"Data Product {product_id} deleted."}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


# ==============================================================================
# 2. Nested Data Asset Operations
# ==============================================================================


def list_assets(
    project_id: str,
    location: str,
    product_id: str,
    page_size: int = 50,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Lists all data assets bundled within a Data Product.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.
        page_size: Number of items per page.
        page_token: Pagination token.

    Returns:
        Dictionary with status and list of assets.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}/dataAssets"
    )
    headers = get_auth_headers()
    params: Dict[str, Any] = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def add_asset(
    project_id: str,
    location: str,
    product_id: str,
    asset_id: str,
    resource: str
) -> Dict[str, Any]:
    """Adds a physical resource (table, view, bucket) as a Data Asset.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.
        asset_id: Unique asset ID within product.
        resource: Google Cloud resource URI (e.g.
            //bigquery.googleapis.com/projects/.../datasets/.../tables/...).

    Returns:
        Dictionary containing created asset details or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}/dataAssets?data_asset_id={asset_id}"
    )
    headers = get_auth_headers()
    payload = {"resource": resource}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def get_asset(
    project_id: str,
    location: str,
    product_id: str,
    asset_id: str
) -> Dict[str, Any]:
    """Retrieves details of a bundled data asset.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.
        asset_id: Unique data asset ID.

    Returns:
        Dictionary containing asset metadata or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}/dataAssets/{asset_id}"
    )
    headers = get_auth_headers()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def remove_asset(
    project_id: str,
    location: str,
    product_id: str,
    asset_id: str
) -> Dict[str, Any]:
    """Removes a data asset from a Data Product.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.
        asset_id: Unique data asset ID.

    Returns:
        Dictionary with status ok or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}/dataAssets/{asset_id}"
    )
    headers = get_auth_headers()
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return {"status": "ok", "message": f"Asset {asset_id} removed from {product_id}."}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


# ==============================================================================
# 3. Access Groups & Permission Management
# ==============================================================================


def configure_access_group(
    project_id: str,
    location: str,
    product_id: str,
    group_id: str,
    display_name: str,
    principal_group: Optional[str] = None,
    principal_user: Optional[str] = None,
    access_groups_json: Optional[str] = None
) -> Dict[str, Any]:
    """Configures access groups on a Data Product.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.
        group_id: Access group ID (e.g., 'analyst').
        display_name: Title for the access group.
        principal_group: Google Group email address.
        principal_user: User email address.
        access_groups_json: Optional raw JSON string for full access_groups dict.

    Returns:
        Dictionary containing updated product or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}?update_mask=access_groups"
    )
    headers = get_auth_headers()

    if access_groups_json:
        try:
            groups_dict = json.loads(access_groups_json)
        except json.JSONDecodeError as err:
            return {"status": "error", "message": f"Invalid JSON: {err}"}
    else:
        principal_dict: Dict[str, str] = {}
        if principal_group:
            principal_dict["google_group"] = principal_group
        elif principal_user:
            principal_dict["user"] = principal_user
        else:
            return {
                "status": "error",
                "message": "Must provide either principal_group or principal_user."
            }

        groups_dict = {
            group_id: {
                "id": group_id,
                "display_name": display_name,
                "principal": principal_dict,
            }
        }

    payload = {"access_groups": groups_dict}

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def set_asset_permissions(
    project_id: str,
    location: str,
    product_id: str,
    asset_id: str,
    group_id: Optional[str] = None,
    iam_roles: Optional[List[str]] = None,
    configs_json: Optional[str] = None
) -> Dict[str, Any]:
    """Configures IAM role permissions for access groups on a specific asset.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.
        asset_id: Unique data asset ID.
        group_id: Access group ID mapped to the asset.
        iam_roles: List of IAM roles to grant (e.g. ['roles/bigquery.dataViewer']).
        configs_json: Optional raw JSON string for access_group_configs.

    Returns:
        Dictionary containing updated asset or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}/dataAssets/{asset_id}?update_mask=access_group_configs"
    )
    headers = get_auth_headers()

    if configs_json:
        try:
            configs_dict = json.loads(configs_json)
        except json.JSONDecodeError as err:
            return {"status": "error", "message": f"Invalid JSON: {err}"}
    else:
        if not group_id or not iam_roles:
            return {
                "status": "error",
                "message": "Both group_id and iam_roles are required when not using configs_json."
            }
        configs_dict = {
            group_id: {
                "iam_roles": iam_roles
            }
        }

    payload = {"access_group_configs": configs_dict}

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


# ==============================================================================
# 4. Governance Workflows (Access Approvals & Requests)
# ==============================================================================


def request_access(
    project_id: str,
    location: str,
    product_id: str,
    access_group_id: str,
    justification: str
) -> Dict[str, Any]:
    """Submits a change request to gain access to a Data Product.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        product_id: Unique data product ID.
        access_group_id: ID of the access group requested.
        justification: Business reason for requesting access.

    Returns:
        Dictionary containing created ChangeRequest or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"dataProducts/{product_id}:requestAccess"
    )
    headers = get_auth_headers()
    payload = {
        "changeRequest": {
            "justification": justification,
            "data_product_access_request": {
                "access_group_id": access_group_id
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def list_reviewable_requests(
    project_id: str,
    location: str,
    page_size: int = 50,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Lists pending access change requests awaiting review by the caller.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        page_size: Maximum requests to return.
        page_token: Pagination token.

    Returns:
        Dictionary containing reviewable change requests or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"changeRequests:listReviewable"
    )
    headers = get_auth_headers()
    params: Dict[str, Any] = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def list_my_requests(
    project_id: str,
    location: str,
    page_size: int = 50,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Lists change requests submitted by the caller.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        page_size: Maximum requests to return.
        page_token: Pagination token.

    Returns:
        Dictionary containing caller's change requests or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"changeRequests:listMine"
    )
    headers = get_auth_headers()
    params: Dict[str, Any] = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def get_request(
    project_id: str,
    location: str,
    request_id: str
) -> Dict[str, Any]:
    """Retrieves status and details of a specific change request.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        request_id: Change request identifier.

    Returns:
        Dictionary containing change request metadata or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"changeRequests/{request_id}"
    )
    headers = get_auth_headers()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def approve_request(
    project_id: str,
    location: str,
    request_id: str
) -> Dict[str, Any]:
    """Approves a pending change request.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        request_id: Change request identifier.

    Returns:
        Dictionary containing approved request details or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"changeRequests/{request_id}:approve"
    )
    headers = get_auth_headers()
    try:
        response = requests.post(url, headers=headers, json={})
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def reject_request(
    project_id: str,
    location: str,
    request_id: str,
    comment: Optional[str] = None
) -> Dict[str, Any]:
    """Rejects a pending change request.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        request_id: Change request identifier.
        comment: Rejection rationale or corrective feedback.

    Returns:
        Dictionary containing rejected request details or error.
    """
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/"
        f"changeRequests/{request_id}:reject"
    )
    headers = get_auth_headers()
    payload: Dict[str, Any] = {}
    if comment:
        payload["comment"] = comment

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


# ==============================================================================
# 5. Metadata, Contracts, & Aspects (Catalog Integration)
# ==============================================================================


def add_refresh_cadence(
    project_id: str,
    location: str,
    product_id: str,
    frequency: str
) -> Dict[str, Any]:
    """Attaches a refresh-cadence SLA contract aspect to the Data Product entry.

    Args:
        project_id: GCP project ID or project number.
        location: Region identifier.
        product_id: Unique data product ID.
        frequency: Cadence string (e.g. 'Daily', 'Weekly', 'Hourly', 'Real-time').

    Returns:
        Dictionary containing updated Catalog Entry or error.
    """
    project_number = get_project_number(project_id)
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_number}/locations/{location}/"
        f"entryGroups/@dataplex/entries/projects/{project_number}/locations/"
        f"{location}/dataProducts/{product_id}?updateMask=aspects"
    )
    headers = get_auth_headers()
    payload = {
        "aspects": {
            "dataplex-types.global.refresh-cadence": {
                "aspectType": (
                    "projects/dataplex-types/locations/global/aspectTypes/"
                    "refresh-cadence"
                ),
                "data": {
                    "frequency": frequency
                }
            }
        }
    }

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


def add_documentation(
    project_id: str,
    location: str,
    product_id: str,
    content: str
) -> Dict[str, Any]:
    """Attaches an overview/documentation aspect to the Data Product entry.

    Args:
        project_id: GCP project ID or project number.
        location: Region identifier.
        product_id: Unique data product ID.
        content: Markdown documentation, query samples, or metric definitions.

    Returns:
        Dictionary containing updated Catalog Entry or error.
    """
    project_number = get_project_number(project_id)
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_number}/locations/{location}/"
        f"entryGroups/@dataplex/entries/projects/{project_number}/locations/"
        f"{location}/dataProducts/{product_id}?updateMask=aspects"
    )
    headers = get_auth_headers()
    payload = {
        "aspects": {
            "dataplex-types.global.overview": {
                "aspectType": (
                    "projects/dataplex-types/locations/global/aspectTypes/overview"
                ),
                "data": {
                    "content": content
                }
            }
        }
    }

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP Error %s: %s", err.response.status_code, err.response.text)
        return {"status": "error", "message": err.response.text}


# ==============================================================================
# CLI Argument Parser
# ==============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Builds the command-line argument parser for product_manager.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Dataplex Data Product Manager CLI"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommands")

    # 1. list-products
    p_list = subparsers.add_parser("list-products", help="List all Data Products")
    p_list.add_argument("--project_id", required=True, help="GCP project ID")
    p_list.add_argument("--location", required=True, help="Region identifier")
    p_list.add_argument("--page_size", type=int, default=50, help="Page size")

    # 2. create-product
    p_create = subparsers.add_parser("create-product", help="Create a Data Product")
    p_create.add_argument("--project_id", required=True, help="GCP project ID")
    p_create.add_argument("--location", required=True, help="Region identifier")
    p_create.add_argument("--product_id", required=True, help="Data Product ID")
    p_create.add_argument("--display_name", required=True, help="Display name")
    p_create.add_argument("--description", required=True, help="Description")
    p_create.add_argument(
        "--owner_emails",
        help="Comma-separated owner email addresses"
    )
    p_create.add_argument(
        "--approver_emails",
        help="Comma-separated approver email addresses"
    )

    # 3. get-product
    p_get = subparsers.add_parser("get-product", help="Get Data Product details")
    p_get.add_argument("--project_id", required=True, help="GCP project ID")
    p_get.add_argument("--location", required=True, help="Region identifier")
    p_get.add_argument("--product_id", required=True, help="Data Product ID")

    # 4. update-product
    p_update = subparsers.add_parser("update-product", help="Update Data Product")
    p_update.add_argument("--project_id", required=True, help="GCP project ID")
    p_update.add_argument("--location", required=True, help="Region identifier")
    p_update.add_argument("--product_id", required=True, help="Data Product ID")
    p_update.add_argument("--display_name", help="New display name")
    p_update.add_argument("--description", help="New description")
    p_update.add_argument("--owner_emails", help="Comma-separated owner emails")
    p_update.add_argument("--approver_emails", help="Comma-separated approver emails")

    # 5. delete-product
    p_delete = subparsers.add_parser("delete-product", help="Delete empty Data Product")
    p_delete.add_argument("--project_id", required=True, help="GCP project ID")
    p_delete.add_argument("--location", required=True, help="Region identifier")
    p_delete.add_argument("--product_id", required=True, help="Data Product ID")

    # 6. list-assets
    a_list = subparsers.add_parser("list-assets", help="List bundled data assets")
    a_list.add_argument("--project_id", required=True, help="GCP project ID")
    a_list.add_argument("--location", required=True, help="Region identifier")
    a_list.add_argument("--product_id", required=True, help="Data Product ID")
    a_list.add_argument("--page_size", type=int, default=50, help="Page size")

    # 7. add-asset
    a_add = subparsers.add_parser("add-asset", help="Add data asset to product")
    a_add.add_argument("--project_id", required=True, help="GCP project ID")
    a_add.add_argument("--location", required=True, help="Region identifier")
    a_add.add_argument("--product_id", required=True, help="Data Product ID")
    a_add.add_argument("--asset_id", required=True, help="Data asset ID")
    a_add.add_argument(
        "--resource",
        required=True,
        help="Google Cloud resource URI (e.g., //bigquery...)"
    )

    # 8. get-asset
    a_get = subparsers.add_parser("get-asset", help="Get data asset details")
    a_get.add_argument("--project_id", required=True, help="GCP project ID")
    a_get.add_argument("--location", required=True, help="Region identifier")
    a_get.add_argument("--product_id", required=True, help="Data Product ID")
    a_get.add_argument("--asset_id", required=True, help="Data asset ID")

    # 9. remove-asset
    a_rem = subparsers.add_parser("remove-asset", help="Remove data asset from product")
    a_rem.add_argument("--project_id", required=True, help="GCP project ID")
    a_rem.add_argument("--location", required=True, help="Region identifier")
    a_rem.add_argument("--product_id", required=True, help="Data Product ID")
    a_rem.add_argument("--asset_id", required=True, help="Data asset ID")

    # 10. configure-access-group
    ag_conf = subparsers.add_parser(
        "configure-access-group",
        help="Configure persona access groups"
    )
    ag_conf.add_argument("--project_id", required=True, help="GCP project ID")
    ag_conf.add_argument("--location", required=True, help="Region identifier")
    ag_conf.add_argument("--product_id", required=True, help="Data Product ID")
    ag_conf.add_argument("--group_id", default="", help="Access group ID")
    ag_conf.add_argument("--display_name", default="", help="Access group display name")
    ag_conf.add_argument("--principal_group", help="Google Group email")
    ag_conf.add_argument("--principal_user", help="Google user email")
    ag_conf.add_argument("--access_groups_json", help="Raw JSON for access groups")

    # 11. set-asset-permissions
    ap_set = subparsers.add_parser(
        "set-asset-permissions",
        help="Configure asset permissions for access groups"
    )
    ap_set.add_argument("--project_id", required=True, help="GCP project ID")
    ap_set.add_argument("--location", required=True, help="Region identifier")
    ap_set.add_argument("--product_id", required=True, help="Data Product ID")
    ap_set.add_argument("--asset_id", required=True, help="Data asset ID")
    ap_set.add_argument("--group_id", help="Access group ID")
    ap_set.add_argument(
        "--iam_roles",
        help="Comma-separated IAM roles (e.g. roles/bigquery.dataViewer)"
    )
    ap_set.add_argument("--configs_json", help="Raw JSON for configs")

    # 12. request-access
    r_req = subparsers.add_parser("request-access", help="Request access to product")
    r_req.add_argument("--project_id", required=True, help="GCP project ID")
    r_req.add_argument("--location", required=True, help="Region identifier")
    r_req.add_argument("--product_id", required=True, help="Data Product ID")
    r_req.add_argument("--access_group_id", required=True, help="Access group ID")
    r_req.add_argument("--justification", required=True, help="Business reason")

    # 13. list-reviewable-requests
    r_rev = subparsers.add_parser(
        "list-reviewable-requests",
        help="List pending requests to review"
    )
    r_rev.add_argument("--project_id", required=True, help="GCP project ID")
    r_rev.add_argument("--location", required=True, help="Region identifier")
    r_rev.add_argument("--page_size", type=int, default=50, help="Page size")

    # 14. list-my-requests
    r_mine = subparsers.add_parser(
        "list-my-requests",
        help="List caller's submitted requests"
    )
    r_mine.add_argument("--project_id", required=True, help="GCP project ID")
    r_mine.add_argument("--location", required=True, help="Region identifier")
    r_mine.add_argument("--page_size", type=int, default=50, help="Page size")

    # 15. get-request
    r_get = subparsers.add_parser("get-request", help="Get change request details")
    r_get.add_argument("--project_id", required=True, help="GCP project ID")
    r_get.add_argument("--location", required=True, help="Region identifier")
    r_get.add_argument("--request_id", required=True, help="Change request ID")

    # 16. approve-request
    r_app = subparsers.add_parser("approve-request", help="Approve change request")
    r_app.add_argument("--project_id", required=True, help="GCP project ID")
    r_app.add_argument("--location", required=True, help="Region identifier")
    r_app.add_argument("--request_id", required=True, help="Change request ID")

    # 17. reject-request
    r_rej = subparsers.add_parser("reject-request", help="Reject change request")
    r_rej.add_argument("--project_id", required=True, help="GCP project ID")
    r_rej.add_argument("--location", required=True, help="Region identifier")
    r_rej.add_argument("--request_id", required=True, help="Change request ID")
    r_rej.add_argument("--comment", help="Rejection rationale")

    # 18. add-refresh-cadence
    c_cad = subparsers.add_parser(
        "add-refresh-cadence",
        help="Attach refresh-cadence SLA contract aspect"
    )
    c_cad.add_argument("--project_id", required=True, help="GCP project ID")
    c_cad.add_argument("--location", required=True, help="Region identifier")
    c_cad.add_argument("--product_id", required=True, help="Data Product ID")
    c_cad.add_argument(
        "--frequency",
        required=True,
        help="Cadence frequency (Daily, Weekly, Hourly, Real-time)"
    )

    # 19. add-documentation
    c_doc = subparsers.add_parser(
        "add-documentation",
        help="Attach overview/documentation aspect"
    )
    c_doc.add_argument("--project_id", required=True, help="GCP project ID")
    c_doc.add_argument("--location", required=True, help="Region identifier")
    c_doc.add_argument("--product_id", required=True, help="Data Product ID")
    c_doc.add_argument(
        "--content",
        required=True,
        help="Markdown content or sample queries"
    )

    return parser


def main() -> None:
    """Entrypoint for the CLI application."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(1)

    result: Dict[str, Any] = {}

    if args.subcommand == "list-products":
        result = list_products(args.project_id, args.location, args.page_size)
    elif args.subcommand == "create-product":
        owners = [e.strip() for e in args.owner_emails.split(",")] if args.owner_emails else None
        approvers = [e.strip() for e in args.approver_emails.split(",")] if args.approver_emails else None
        result = create_product(
            args.project_id, args.location, args.product_id,
            args.display_name, args.description, owners, approvers
        )
    elif args.subcommand == "get-product":
        result = get_product(args.project_id, args.location, args.product_id)
    elif args.subcommand == "update-product":
        owners = [e.strip() for e in args.owner_emails.split(",")] if args.owner_emails else None
        approvers = [e.strip() for e in args.approver_emails.split(",")] if args.approver_emails else None
        result = update_product(
            args.project_id, args.location, args.product_id,
            args.display_name, args.description, owners, approvers
        )
    elif args.subcommand == "delete-product":
        result = delete_product(args.project_id, args.location, args.product_id)
    elif args.subcommand == "list-assets":
        result = list_assets(args.project_id, args.location, args.product_id, args.page_size)
    elif args.subcommand == "add-asset":
        result = add_asset(args.project_id, args.location, args.product_id, args.asset_id, args.resource)
    elif args.subcommand == "get-asset":
        result = get_asset(args.project_id, args.location, args.product_id, args.asset_id)
    elif args.subcommand == "remove-asset":
        result = remove_asset(args.project_id, args.location, args.product_id, args.asset_id)
    elif args.subcommand == "configure-access-group":
        result = configure_access_group(
            args.project_id, args.location, args.product_id,
            args.group_id, args.display_name, args.principal_group,
            args.principal_user, args.access_groups_json
        )
    elif args.subcommand == "set-asset-permissions":
        roles = [r.strip() for r in args.iam_roles.split(",")] if args.iam_roles else None
        result = set_asset_permissions(
            args.project_id, args.location, args.product_id,
            args.asset_id, args.group_id, roles, args.configs_json
        )
    elif args.subcommand == "request-access":
        result = request_access(
            args.project_id, args.location, args.product_id,
            args.access_group_id, args.justification
        )
    elif args.subcommand == "list-reviewable-requests":
        result = list_reviewable_requests(args.project_id, args.location, args.page_size)
    elif args.subcommand == "list-my-requests":
        result = list_my_requests(args.project_id, args.location, args.page_size)
    elif args.subcommand == "get-request":
        result = get_request(args.project_id, args.location, args.request_id)
    elif args.subcommand == "approve-request":
        result = approve_request(args.project_id, args.location, args.request_id)
    elif args.subcommand == "reject-request":
        result = reject_request(args.project_id, args.location, args.request_id, args.comment)
    elif args.subcommand == "add-refresh-cadence":
        result = add_refresh_cadence(args.project_id, args.location, args.product_id, args.frequency)
    elif args.subcommand == "add-documentation":
        result = add_documentation(args.project_id, args.location, args.product_id, args.content)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

