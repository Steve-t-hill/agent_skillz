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

"""Dataplex Data Domain Manager CLI and REST Client.

This module provides programmatic management of Dataplex Data Domains
and Subdomains in Google Cloud Knowledge Catalog. It handles domain lifecycle,
IAM access control policies, resource authorization and bindings, and scoped
semantic search within domain contexts.
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional
import requests
import google.auth
from google.auth.transport.requests import Request

# Configure logging to stderr so JSON output on stdout remains pristine
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("domain-manager")

TIMEOUT_SECONDS = 30
DATAPLEX_API_BASE = "https://dataplex.googleapis.com/v1"
BIGQUERY_API_BASE = "https://bigquery.googleapis.com/bigquery/v2"


def get_credentials() -> google.auth.credentials.Credentials:
    """Retrieves Google Cloud credentials using Application Default Credentials (ADC).

    Returns:
        A valid google.auth credentials object refreshed if necessary.
    """
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds


def handle_response(response: requests.Response) -> Dict[str, Any]:
    """Handles HTTP responses uniformly across Dataplex REST endpoints.

    Args:
        response: The requests Response object.

    Returns:
        A dictionary with 'status' and either 'data' or error 'message'.
    """
    try:
        response.raise_for_status()
        if response.status_code == 204:
            return {"status": "ok", "message": "Resource deleted successfully"}
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as err:
        logger.error(
            "HTTP Error %s: %s",
            response.status_code,
            response.text
        )
        try:
            err_json = response.json()
            message = err_json.get("error", {}).get("message", str(err))
        except Exception:
            message = response.text or str(err)
        return {"status": "error", "message": message, "code": response.status_code}
    except Exception as err:
        logger.error("Unexpected error: %s", str(err))
        return {"status": "error", "message": str(err)}


# ==============================================================================
# 1. Domain & Subdomain Management (CRUD)
# ==============================================================================

def list_domains(project_id: str, location: str) -> Dict[str, Any]:
    """Lists all Dataplex Data Domains in a given project and location.

    Args:
        project_id: The GCP project ID.
        location: The region (e.g. 'us-central1' or 'global').

    Returns:
        JSON response containing list of domains or error message.
    """
    creds = get_credentials()
    url = f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}/dataDomains"
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    return handle_response(response)


def create_domain(
    project_id: str,
    location: str,
    domain_id: str,
    display_name: str,
    description: str,
    contact_name: Optional[str] = None,
    contact_role: Optional[str] = None,
    contact_email: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new top-level Dataplex Data Domain.

    Args:
        project_id: GCP project ID.
        location: Target location/region.
        domain_id: kebab-case unique identifier for the domain.
        display_name: Human-readable domain name.
        description: Functional description and scope of the domain.
        contact_name: Optional contact display name.
        contact_role: Optional contact role (e.g., 'owner', 'steward').
        contact_email: Optional contact email identifier.

    Returns:
        Created domain metadata or error details.
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains?data_domain_id={domain_id}"
    )
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }
    payload: Dict[str, Any] = {
        "display_name": display_name,
        "description": description,
    }
    if contact_name or contact_email:
        payload["contacts"] = {
            "identities": [
                {
                    "contact_name": contact_name or "Domain Owner",
                    "contact_role": contact_role or "owner",
                    "contact_id": contact_email or ""
                }
            ]
        }
    response = requests.post(
        url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS
    )
    return handle_response(response)


def create_subdomain(
    project_id: str,
    location: str,
    domain_id: str,
    parent_domain_id: str,
    display_name: str,
    description: str,
    contact_name: Optional[str] = None,
    contact_role: Optional[str] = None,
    contact_email: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a Dataplex Data Subdomain nested under an existing parent domain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: kebab-case unique identifier for the subdomain.
        parent_domain_id: Parent domain ID or full resource path.
        display_name: Subdomain display name.
        description: Subdomain purpose and boundaries.
        contact_name: Optional contact name.
        contact_role: Optional contact role.
        contact_email: Optional contact email.

    Returns:
        Created subdomain metadata or error details.
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains?data_domain_id={domain_id}"
    )
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    if parent_domain_id.startswith("projects/"):
        parent_path = parent_domain_id
    else:
        parent_path = (
            f"projects/{project_id}/locations/{location}/dataDomains/"
            f"{parent_domain_id}"
        )

    payload: Dict[str, Any] = {
        "display_name": display_name,
        "description": description,
        "parent_data_domain": parent_path
    }
    if contact_name or contact_email:
        payload["contacts"] = {
            "identities": [
                {
                    "contact_name": contact_name or "Subdomain Owner",
                    "contact_role": contact_role or "owner",
                    "contact_id": contact_email or ""
                }
            ]
        }

    response = requests.post(
        url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS
    )
    return handle_response(response)


def get_domain(project_id: str, location: str, domain_id: str) -> Dict[str, Any]:
    """Retrieves full metadata for a specific Data Domain or Subdomain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.

    Returns:
        Domain details including policyMember (domain principal).
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains/{domain_id}"
    )
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    return handle_response(response)


def list_subdomains(
    project_id: str,
    location: str,
    domain_id: str
) -> Dict[str, Any]:
    """Lists all child subdomains for a parent domain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Parent domain identifier.

    Returns:
        List of child subdomains.
    """
    creds = get_credentials()
    parent_path = (
        f"projects/{project_id}/locations/{location}/dataDomains/{domain_id}"
    )
    # Dataplex supports subdomains resource collection and filtering by parent
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains/{domain_id}/subdomains"
    )
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)

    # Fall back to parent filter if the direct subdomains endpoint is not exposed
    if response.status_code == 404:
        filter_query = f'parent_data_domain="{parent_path}"'
        alt_url = (
            f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
            f"/dataDomains?filter={filter_query}"
        )
        response = requests.get(
            alt_url, headers=headers, timeout=TIMEOUT_SECONDS
        )

    return handle_response(response)


def update_domain(
    project_id: str,
    location: str,
    domain_id: str,
    description: Optional[str] = None,
    display_name: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Updates mutable properties of an existing Data Domain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.
        description: New description text.
        display_name: New display name.
        labels: Dictionary of labels to apply.

    Returns:
        Updated domain object.
    """
    update_masks: List[str] = []
    payload: Dict[str, Any] = {}

    if description is not None:
        payload["description"] = description
        update_masks.append("description")
    if display_name is not None:
        payload["display_name"] = display_name
        update_masks.append("display_name")
    if labels is not None:
        payload["labels"] = labels
        update_masks.append("labels")

    if not update_masks:
        return {"status": "error", "message": "No update fields specified."}

    creds = get_credentials()

    mask_str = ",".join(update_masks)
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains/{domain_id}?updateMask={mask_str}"
    )
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }
    response = requests.patch(
        url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS
    )
    return handle_response(response)


def delete_domain(project_id: str, location: str, domain_id: str) -> Dict[str, Any]:
    """Deletes an empty Dataplex Data Domain or Subdomain.

    Note: The domain must have 0 child subdomains and 0 resource bindings.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.

    Returns:
        Success message or error if domain is not empty.
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains/{domain_id}"
    )
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.delete(url, headers=headers, timeout=TIMEOUT_SECONDS)
    return handle_response(response)


# ==============================================================================
# 2. IAM & Access Control (Domain Level)
# ==============================================================================

def get_iam_policy(
    project_id: str,
    location: str,
    domain_id: str
) -> Dict[str, Any]:
    """Gets the IAM access control policy for a domain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.

    Returns:
        IAM policy representation with bindings and etag.
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains/{domain_id}:getIamPolicy"
    )
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json={}, timeout=TIMEOUT_SECONDS)
    return handle_response(response)


def set_iam_policy(
    project_id: str,
    location: str,
    domain_id: str,
    policy: Dict[str, Any]
) -> Dict[str, Any]:
    """Sets or replaces the IAM access control policy for a domain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.
        policy: IAM policy dictionary containing 'bindings'.

    Returns:
        Updated IAM policy object.
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains/{domain_id}:setIamPolicy"
    )
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }
    payload = {"policy": policy}
    response = requests.post(
        url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS
    )
    return handle_response(response)


def add_iam_member(
    project_id: str,
    location: str,
    domain_id: str,
    role: str,
    member: str
) -> Dict[str, Any]:
    """Adds an IAM member binding to a domain's access policy.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.
        role: Target IAM role (e.g., 'roles/dataplex.dataDomainViewer').
        member: Member identity (e.g., 'user:alice@example.com').

    Returns:
        Updated policy response.
    """
    current_resp = get_iam_policy(project_id, location, domain_id)
    if current_resp.get("status") != "ok":
        return current_resp

    policy = current_resp.get("data", {})
    bindings = policy.get("bindings", [])

    # Find existing binding for this role or append new binding
    matched_binding = None
    for binding in bindings:
        if binding.get("role") == role:
            matched_binding = binding
            break

    if matched_binding:
        members = matched_binding.setdefault("members", [])
        if member not in members:
            members.append(member)
    else:
        bindings.append({"role": role, "members": [member]})

    policy["bindings"] = bindings
    return set_iam_policy(project_id, location, domain_id, policy)


# ==============================================================================
# 3. Resource Authorization & Binding (Inclusion)
# ==============================================================================

def get_domain_principal(
    project_id: str,
    location: str,
    domain_id: str
) -> Dict[str, Any]:
    """Retrieves the domain's IAM principal identity (policyMember).

    This identity is used in Step B to grant permissions on target resources.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.

    Returns:
        Dictionary containing 'principal' or error message.
    """
    domain_resp = get_domain(project_id, location, domain_id)
    if domain_resp.get("status") != "ok":
        return domain_resp

    data = domain_resp.get("data", {})
    principal = data.get("policyMember") or data.get("policy_member")
    if not principal:
        return {
            "status": "error",
            "message": "Domain does not contain a 'policyMember' principal."
        }
    return {
        "status": "ok",
        "principal": principal,
        "domain_id": domain_id
    }


def authorize_dataset(
    project_id: str,
    dataset_id: str,
    principal: str,
    role: str = "roles/bigquery.metadataViewer"
) -> Dict[str, Any]:
    """Grants the domain principal access to a BigQuery dataset (Step B helper).

    Args:
        project_id: BigQuery project ID.
        dataset_id: Target dataset ID.
        principal: Domain principal (e.g., 'serviceAccount:...' or 'user:...').
        role: IAM role to grant on the dataset.

    Returns:
        Status of the dataset access update.
    """
    creds = get_credentials()
    get_url = f"{BIGQUERY_API_BASE}/projects/{project_id}/datasets/{dataset_id}"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    resp = requests.get(get_url, headers=headers, timeout=TIMEOUT_SECONDS)
    if resp.status_code != 200:
        return handle_response(resp)

    dataset_meta = resp.json()
    access_list = dataset_meta.get("access", [])

    # Extract member type and email if formatted like serviceAccount:foo@bar.com
    access_entry: Dict[str, str] = {"role": role}
    if principal.startswith("serviceAccount:"):
        access_entry["userByEmail"] = principal.replace("serviceAccount:", "")
    elif principal.startswith("user:"):
        access_entry["userByEmail"] = principal.replace("user:", "")
    elif principal.startswith("group:"):
        access_entry["groupByEmail"] = principal.replace("group:", "")
    else:
        access_entry["iamMember"] = principal

    # Check if entry already exists
    already_present = any(
        entry.get("role") == role and (
            (access_entry.get("userByEmail") and entry.get("userByEmail") == access_entry.get("userByEmail")) or
            (access_entry.get("groupByEmail") and entry.get("groupByEmail") == access_entry.get("groupByEmail")) or
            (access_entry.get("iamMember") and entry.get("iamMember") == access_entry.get("iamMember"))
        )
        for entry in access_list
    )

    if not already_present:
        access_list.append(access_entry)
        patch_payload = {"access": access_list}
        patch_resp = requests.patch(
            get_url, headers=headers, json=patch_payload, timeout=TIMEOUT_SECONDS
        )
        return handle_response(patch_resp)

    return {"status": "ok", "message": "Domain principal already authorized on dataset."}


def authorize_table(
    project_id: str,
    dataset_id: str,
    table_id: str,
    principal: str,
    role: str = "roles/bigquery.metadataViewer"
) -> Dict[str, Any]:
    """Grants IAM role on a specific BigQuery table to the domain policyMember principal.

    Args:
        project_id: GCP project ID hosting the dataset.
        dataset_id: Target BigQuery dataset ID.
        table_id: Target BigQuery table ID.
        principal: Full principal string (e.g., 'principal://dataplex...').
        role: IAM role to grant (default: 'roles/bigquery.metadataViewer').

    Returns:
        BigQuery IAM policy response or status message.
    """
    creds = get_credentials()
    get_url = f"{BIGQUERY_API_BASE}/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}:getIamPolicy"
    set_url = f"{BIGQUERY_API_BASE}/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}:setIamPolicy"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    # Fetch existing table IAM policy
    get_resp = requests.post(get_url, headers=headers, json={}, timeout=TIMEOUT_SECONDS)
    if get_resp.status_code != 200:
        return handle_response(get_resp)

    policy = get_resp.json()
    bindings = policy.get("bindings", [])

    # Check if role binding already exists
    role_binding = next((b for b in bindings if b.get("role") == role), None)
    if role_binding:
        if principal in role_binding.get("members", []):
            return {"status": "ok", "message": "Domain principal already authorized on table."}
        role_binding.setdefault("members", []).append(principal)
    else:
        bindings.append({
            "role": role,
            "members": [principal]
        })

    policy["bindings"] = bindings
    set_resp = requests.post(
        set_url,
        headers=headers,
        json={"policy": policy},
        timeout=TIMEOUT_SECONDS
    )
    return handle_response(set_resp)


def bind_resource(
    project_id: str,
    location: str,
    domain_id: str,
    binding_id: str,
    resource: str
) -> Dict[str, Any]:
    """Binds an authorized physical resource (BigQuery dataset, Project) to a domain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.
        binding_id: Unique identifier for this binding.
        resource: Fully qualified resource URI:
          - BigQuery: '//bigquery.googleapis.com/projects/{P}/datasets/{D}'
          - Project: '//cloudresourcemanager.googleapis.com/projects/{P}'

    Returns:
        Created binding metadata.
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains/{domain_id}/bindings?data_domain_binding_id={binding_id}"
    )
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }
    payload = {"resource": resource}
    response = requests.post(
        url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS
    )
    return handle_response(response)


def list_bindings(
    project_id: str,
    location: str,
    domain_id: str
) -> Dict[str, Any]:
    """Lists all resources currently bound to a domain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.

    Returns:
        List of binding items.
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains/{domain_id}/bindings"
    )
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    return handle_response(response)


def unbind_resource(
    project_id: str,
    location: str,
    domain_id: str,
    binding_id: str
) -> Dict[str, Any]:
    """Removes a bound resource from a domain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.
        binding_id: Identifier of the binding to delete.

    Returns:
        Deletion confirmation message.
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}"
        f"/dataDomains/{domain_id}/bindings/{binding_id}"
    )
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.delete(url, headers=headers, timeout=TIMEOUT_SECONDS)
    return handle_response(response)


# ==============================================================================
# 4. Scoped Search within Domains
# ==============================================================================

def search_entries(
    project_id: str,
    location: str,
    domain_id: str,
    query: str,
    semantic_search: bool = True,
    page_size: int = 100
) -> Dict[str, Any]:
    """Performs scoped search across Knowledge Catalog entries within a domain.

    Args:
        project_id: GCP project ID.
        location: Region identifier.
        domain_id: Target domain identifier.
        query: Search term or natural language inquiry.
        semantic_search: Whether to execute AI-assisted semantic search.
        page_size: Maximum entries to return.

    Returns:
        List of matching catalog entries.
    """
    creds = get_credentials()
    url = (
        f"{DATAPLEX_API_BASE}/projects/{project_id}/locations/{location}:searchEntries"
    )
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "contexts": [
            f"projects/{project_id}/locations/{location}/dataDomains/{domain_id}"
        ],
        "semantic_search": semantic_search,
        "page_size": page_size
    }
    response = requests.post(
        url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS
    )
    return handle_response(response)


# ==============================================================================
# 5. Domain Overview Documentation (Aspect Management)
# ==============================================================================

def set_overview(
    project_id: str,
    location: str,
    domain_id: str,
    content: str,
    content_type: str = "MARKDOWN"
) -> Dict[str, Any]:
    """Updates the native Knowledge Catalog Overview aspect on a Data Domain entry.

    Args:
        project_id: GCP project ID or project number.
        location: Region identifier.
        domain_id: Data domain identifier.
        content: Markdown / HTML text content for the Overview.
        content_type: 'MARKDOWN' or 'HTML' (default: 'MARKDOWN').

    Returns:
        Updated Dataplex Entry metadata.
    """
    creds = get_credentials()
    domain_info = get_domain(project_id, location, domain_id)
    if domain_info.get("status") == "error":
        return domain_info

    domain_data = domain_info.get("data", {})
    policy_member = domain_data.get("policyMember", {})
    principal = policy_member.get("iamPolicyNamePrincipal", "")
    if "/projects/" in principal:
        proj_num = principal.split("/projects/")[1].split("/")[0]
    else:
        proj_num = project_id

    entry_name = f"projects/{proj_num}/locations/{location}/entryGroups/@dataplex/entries/projects/{proj_num}/locations/{location}/dataDomains/{domain_id}"
    entry_url = f"{DATAPLEX_API_BASE}/{entry_name}?updateMask=aspects"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }
    payload = {
        "aspects": {
            "655216118709.global.overview": {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/overview",
                "data": {
                    "content": content,
                    "contentType": content_type.upper()
                }
            }
        }
    }
    resp = requests.patch(entry_url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
    return handle_response(resp)


def get_overview(
    project_id: str,
    location: str,
    domain_id: str
) -> Dict[str, Any]:
    """Retrieves the native Knowledge Catalog Overview aspect for a Data Domain entry."""
    creds = get_credentials()
    domain_info = get_domain(project_id, location, domain_id)
    if domain_info.get("status") == "error":
        return domain_info

    domain_data = domain_info.get("data", {})
    policy_member = domain_data.get("policyMember", {})
    principal = policy_member.get("iamPolicyNamePrincipal", "")
    if "/projects/" in principal:
        proj_num = principal.split("/projects/")[1].split("/")[0]
    else:
        proj_num = project_id

    entry_name = f"projects/{proj_num}/locations/{location}/entryGroups/@dataplex/entries/projects/{proj_num}/locations/{location}/dataDomains/{domain_id}"
    entry_url = f"{DATAPLEX_API_BASE}/{entry_name}?view=FULL"
    headers = {"Authorization": f"Bearer {creds.token}"}
    resp = requests.get(entry_url, headers=headers, timeout=TIMEOUT_SECONDS)
    if resp.status_code == 200:
        aspects = resp.json().get("aspects", {})
        overview = None
        for k, v in aspects.items():
            if k.endswith(".overview") or k.endswith(".global.overview"):
                overview = v
                break
        if overview:
            return {"status": "ok", "overview": overview.get("data", {}).get("content", "")}
        return {"status": "ok", "overview": None, "message": "No Overview aspect attached."}
    return handle_response(resp)


# ==============================================================================
# CLI Argument Parser & Entrypoint
# ==============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Builds and returns the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Dataplex Data Domain Manager CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # --- Domain CRUD ---
    p = subparsers.add_parser("list-domains", help="List all data domains")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")

    p = subparsers.add_parser("create-domain", help="Create a top-level data domain")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID (kebab-case)")
    p.add_argument("--display_name", required=True, help="Display name")
    p.add_argument("--description", required=True, help="Domain description")
    p.add_argument("--contact_name", help="Contact person name")
    p.add_argument("--contact_role", default="owner", help="Contact role")
    p.add_argument("--contact_email", help="Contact email address")

    p = subparsers.add_parser("create-subdomain", help="Create a nested subdomain")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Subdomain ID (kebab-case)")
    p.add_argument("--parent_domain_id", required=True, help="Parent domain ID")
    p.add_argument("--display_name", required=True, help="Display name")
    p.add_argument("--description", required=True, help="Subdomain description")
    p.add_argument("--contact_name", help="Contact person name")
    p.add_argument("--contact_role", default="owner", help="Contact role")
    p.add_argument("--contact_email", help="Contact email address")

    p = subparsers.add_parser("get-domain", help="Get details of a domain")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")

    p = subparsers.add_parser("list-subdomains", help="List subdomains of a parent")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Parent domain ID")

    p = subparsers.add_parser("update-domain", help="Update domain metadata")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")
    p.add_argument("--display_name", help="Updated display name")
    p.add_argument("--description", help="Updated description")
    p.add_argument("--labels", help="JSON string of labels dict")

    p = subparsers.add_parser("delete-domain", help="Delete an empty domain")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")

    # --- IAM ---
    p = subparsers.add_parser("get-iam-policy", help="Get domain IAM policy")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")

    p = subparsers.add_parser("set-iam-policy", help="Set domain IAM policy")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")
    p.add_argument("--policy_json", required=True, help="JSON policy string")

    p = subparsers.add_parser("add-iam-member", help="Add IAM member to domain")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")
    p.add_argument("--role", required=True, help="IAM role")
    p.add_argument("--member", required=True, help="Member identity")

    # --- Bindings ---
    p = subparsers.add_parser(
        "get-domain-principal",
        help="Get policyMember principal identity"
    )
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")

    p = subparsers.add_parser(
        "authorize-dataset",
        help="Grant domain principal access on target BQ dataset"
    )
    p.add_argument("--project_id", required=True, help="Target project ID")
    p.add_argument("--dataset_id", required=True, help="Target dataset ID")
    p.add_argument("--principal", required=True, help="Domain policyMember principal")
    p.add_argument(
        "--role",
        default="roles/bigquery.metadataViewer",
        help="Role to grant"
    )

    p = subparsers.add_parser(
        "authorize-table",
        help="Grant domain principal access on target BQ table"
    )
    p.add_argument("--project_id", required=True, help="Target project ID")
    p.add_argument("--dataset_id", required=True, help="Target dataset ID")
    p.add_argument("--table_id", required=True, help="Target table ID")
    p.add_argument("--principal", required=True, help="Domain policyMember principal")
    p.add_argument(
        "--role",
        default="roles/bigquery.metadataViewer",
        help="Role to grant"
    )

    p = subparsers.add_parser("bind-resource", help="Bind resource to domain")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")
    p.add_argument("--binding_id", required=True, help="Unique binding ID")
    p.add_argument(
        "--resource",
        required=True,
        help="Resource URI (//bigquery... or //cloudresourcemanager...)"
    )

    p = subparsers.add_parser("list-bindings", help="List resources in domain")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")

    p = subparsers.add_parser("unbind-resource", help="Unbind resource from domain")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")
    p.add_argument("--binding_id", required=True, help="Binding ID to delete")

    # --- Search ---
    p = subparsers.add_parser("search-entries", help="Search entries in domain")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")
    p.add_argument("--query", required=True, help="Search query string")
    p.add_argument(
        "--semantic_search",
        type=lambda v: str(v).lower() in ("true", "1", "yes"),
        default=True,
        help="Enable semantic search (default: true)"
    )
    p.add_argument("--page_size", type=int, default=100, help="Page size")

    # --- Overview Documentation ---
    p = subparsers.add_parser("set-overview", help="Set domain Overview aspect content")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")
    p.add_argument("--content", required=True, help="Overview content string (Markdown/HTML)")
    p.add_argument(
        "--content_type",
        choices=["MARKDOWN", "HTML"],
        default="MARKDOWN",
        help="Overview format: MARKDOWN or HTML (default: MARKDOWN)"
    )

    p = subparsers.add_parser("get-overview", help="Get domain Overview aspect content")
    p.add_argument("--project_id", required=True, help="GCP project ID")
    p.add_argument("--location", required=True, help="Region identifier")
    p.add_argument("--domain_id", required=True, help="Domain ID")

    return parser


def main() -> None:
    """CLI execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    result: Dict[str, Any] = {}

    if args.command == "list-domains":
        result = list_domains(args.project_id, args.location)
    elif args.command == "create-domain":
        result = create_domain(
            args.project_id,
            args.location,
            args.domain_id,
            args.display_name,
            args.description,
            args.contact_name,
            args.contact_role,
            args.contact_email
        )
    elif args.command == "create-subdomain":
        result = create_subdomain(
            args.project_id,
            args.location,
            args.domain_id,
            args.parent_domain_id,
            args.display_name,
            args.description,
            args.contact_name,
            args.contact_role,
            args.contact_email
        )
    elif args.command == "get-domain":
        result = get_domain(args.project_id, args.location, args.domain_id)
    elif args.command == "list-subdomains":
        result = list_subdomains(args.project_id, args.location, args.domain_id)
    elif args.command == "update-domain":
        labels_dict = json.loads(args.labels) if args.labels else None
        result = update_domain(
            args.project_id,
            args.location,
            args.domain_id,
            args.description,
            args.display_name,
            labels_dict
        )
    elif args.command == "delete-domain":
        result = delete_domain(args.project_id, args.location, args.domain_id)
    elif args.command == "get-iam-policy":
        result = get_iam_policy(args.project_id, args.location, args.domain_id)
    elif args.command == "set-iam-policy":
        policy_dict = json.loads(args.policy_json)
        result = set_iam_policy(
            args.project_id, args.location, args.domain_id, policy_dict
        )
    elif args.command == "add-iam-member":
        result = add_iam_member(
            args.project_id, args.location, args.domain_id, args.role, args.member
        )
    elif args.command == "get-domain-principal":
        result = get_domain_principal(
            args.project_id, args.location, args.domain_id
        )
    elif args.command == "authorize-dataset":
        result = authorize_dataset(
            args.project_id, args.dataset_id, args.principal, args.role
        )
    elif args.command == "authorize-table":
        result = authorize_table(
            args.project_id, args.dataset_id, args.table_id, args.principal, args.role
        )
    elif args.command == "bind-resource":
        result = bind_resource(
            args.project_id,
            args.location,
            args.domain_id,
            args.binding_id,
            args.resource
        )
    elif args.command == "list-bindings":
        result = list_bindings(args.project_id, args.location, args.domain_id)
    elif args.command == "unbind-resource":
        result = unbind_resource(
            args.project_id, args.location, args.domain_id, args.binding_id
        )
    elif args.command == "search-entries":
        result = search_entries(
            args.project_id,
            args.location,
            args.domain_id,
            args.query,
            args.semantic_search,
            args.page_size
        )
    elif args.command == "set-overview":
        result = set_overview(
            args.project_id,
            args.location,
            args.domain_id,
            args.content,
            args.content_type
        )
    elif args.command == "get-overview":
        result = get_overview(
            args.project_id,
            args.location,
            args.domain_id
        )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
