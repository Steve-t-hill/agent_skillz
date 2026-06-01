#  Copyright 2025 Steve Thill
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

import argparse
import json
import logging
import sys
import time
import requests
import google.auth
from google.auth.transport.requests import Request

# Configure logging to stderr so it doesn't interfere with JSON output
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s: %(message)s')
logger = logging.getLogger("glossary-manager")

TIMEOUT_SECONDS = 30

def get_credentials():
    """Gets Google Cloud credentials using ADC."""
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    if not creds.valid:
        creds.refresh(Request())
    return creds

def get_project_number(project_id):
    """Retrieves the project number for a given project ID using Cloud Resource Manager API."""
    creds = get_credentials()
    url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}"
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()["projectNumber"]

def handle_response(response):
    """Generic handler for API responses."""
    try:
        response.raise_for_status()
        if response.status_code == 204:
            return {"status": "ok", "message": "Resource deleted successfully"}
        return {"status": "ok", "data": response.json()}
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} {e.response.text}")
        try:
            error_data = e.response.json()
            message = error_data.get("error", {}).get("message", str(e))
        except:
            message = str(e)
        return {"status": "error", "message": message}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"status": "error", "message": str(e)}

# --- Glossary Functions ---

def list_glossaries(project_id, location):
    creds = get_credentials()
    url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/glossaries"
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def create_glossary(project_id, location, glossary_id, display_name, description):
    creds = get_credentials()
    url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/glossaries?glossary_id={glossary_id}"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {"displayName": display_name, "description": description}
    response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def get_glossary(project_id, location, glossary_id):
    creds = get_credentials()
    url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/glossaries/{glossary_id}"
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def add_glossary_overview(project_id, location, glossary_id, overview):
    creds = get_credentials()
    project_number = get_project_number(project_id)
    url = f"https://dataplex.googleapis.com/v1/projects/{project_number}/locations/{location}/entryGroups/%40dataplex/entries/projects/{project_number}/locations/{location}/glossaries/{glossary_id}?update_mask=aspects&deleteMissingAspects=false&aspect_keys=projects/dataplex-types/locations/global/aspectTypes/overview"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {
        "aspects": {
            "dataplex-types.global.overview": {
                "aspect_type": "projects/dataplex-types/locations/global/aspectTypes/overview",
                "data": {"content": overview, "links": []}
            }
        }
    }
    response = requests.patch(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

# --- Category Functions ---

def list_categories(project_id, location, glossary_id):
    creds = get_credentials()
    url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/glossaries/{glossary_id}/categories"
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def create_category(project_id, location, glossary_id, category_id, display_name, description, parent_category_id=None):
    creds = get_credentials()
    url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/glossaries/{glossary_id}/categories?category_id={category_id}"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {"displayName": display_name, "description": description}
    if parent_category_id:
        data["parent"] = f"projects/{project_id}/locations/{location}/glossaries/{glossary_id}/categories/{parent_category_id}"
    else:
        data["parent"] = f"projects/{project_id}/locations/{location}/glossaries/{glossary_id}"
    response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def add_category_overview(project_id, location, glossary_id, category_id, overview):
    creds = get_credentials()
    project_number = get_project_number(project_id)
    url = f"https://dataplex.googleapis.com/v1/projects/{project_number}/locations/{location}/entryGroups/%40dataplex/entries/projects/{project_number}/locations/{location}/glossaries/{glossary_id}/categories/{category_id}?update_mask=aspects&deleteMissingAspects=false&aspect_keys=projects/dataplex-types/locations/global/aspectTypes/overview"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {
        "aspects": {
            "dataplex-types.global.overview": {
                "aspect_type": "projects/dataplex-types/locations/global/aspectTypes/overview",
                "data": {"content": overview, "links": []}
            }
        }
    }
    response = requests.patch(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def add_category_contacts(project_id, location, glossary_id, category_id, contact_name, contact_email):
    creds = get_credentials()
    project_number = get_project_number(project_id)
    url = f"https://dataplex.googleapis.com/v1/projects/{project_number}/locations/{location}/entryGroups/%40dataplex/entries/projects/{project_number}/locations/{location}/glossaries/{glossary_id}/categories/{category_id}?update_mask=aspects&deleteMissingAspects=false&aspect_keys=projects/dataplex-types/locations/global/aspectTypes/contacts"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {
        "aspects": {
            "dataplex-types.global.contacts": {
                "aspect_type": "projects/dataplex-types/locations/global/aspectTypes/contacts",
                "data": {
                    "identities": [{"role": "steward", "name": contact_name, "id": contact_email}]
                }
            }
        }
    }
    response = requests.patch(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

# --- Term Functions ---

def list_terms(project_id, location, glossary_id):
    creds = get_credentials()
    url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/glossaries/{glossary_id}/terms"
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def create_term(project_id, location, glossary_id, term_id, display_name, description, parent_category_id=None):
    creds = get_credentials()
    url = f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{location}/glossaries/{glossary_id}/terms?term_id={term_id}"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {"displayName": display_name, "description": description}
    if parent_category_id:
        data["parent"] = f"projects/{project_id}/locations/{location}/glossaries/{glossary_id}/categories/{parent_category_id}"
    else:
        data["parent"] = f"projects/{project_id}/locations/{location}/glossaries/{glossary_id}"
    response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def add_term_overview(project_id, location, glossary_id, term_id, overview):
    creds = get_credentials()
    project_number = get_project_number(project_id)
    url = f"https://dataplex.googleapis.com/v1/projects/{project_number}/locations/{location}/entryGroups/%40dataplex/entries/projects/{project_number}/locations/{location}/glossaries/{glossary_id}/terms/{term_id}?update_mask=aspects&deleteMissingAspects=false&aspect_keys=projects/dataplex-types/locations/global/aspectTypes/overview"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {
        "aspects": {
            "dataplex-types.global.overview": {
                "aspect_type": "projects/dataplex-types/locations/global/aspectTypes/overview",
                "data": {"content": overview, "links": []}
            }
        }
    }
    response = requests.patch(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def add_term_contacts(project_id, location, glossary_id, term_id, contact_name, contact_email):
    creds = get_credentials()
    project_number = get_project_number(project_id)
    url = f"https://dataplex.googleapis.com/v1/projects/{project_number}/locations/{location}/entryGroups/%40dataplex/entries/projects/{project_number}/locations/{location}/glossaries/{glossary_id}/terms/{term_id}?update_mask=aspects&deleteMissingAspects=false&aspect_keys=projects/dataplex-types/locations/global/aspectTypes/contacts"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {
        "aspects": {
            "dataplex-types.global.contacts": {
                "aspect_type": "projects/dataplex-types/locations/global/aspectTypes/contacts",
                "data": {
                    "identities": [{"role": "steward", "name": contact_name, "id": contact_email}]
                }
            }
        }
    }
    response = requests.patch(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

# --- Linking Functions ---

def attach_term_to_data_asset(project_id, entry_location_id, entry_group_id, entry_id, term_project_id, term_location_id, term_glossary_id, term_id, entry_link_id):
    creds = get_credentials()
    project_number = get_project_number(project_id)
    term_project_number = get_project_number(term_project_id)
    url = f"https://dataplex.googleapis.com/v1/projects/{project_number}/locations/{entry_location_id}/entryGroups/{entry_group_id}/entryLinks?entry_link_id={entry_link_id}"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {
        "entry_link_type": "projects/dataplex-types/locations/global/entryLinkTypes/definition",
        "entry_references": [
            {"name": f"projects/{project_number}/locations/{entry_location_id}/entryGroups/{entry_group_id}/entries/{entry_id}", "type": "SOURCE"},
            {"name": f"projects/{term_project_number}/locations/{term_location_id}/entryGroups/%40dataplex/entries/projects/{term_project_number}/locations/{term_location_id}/glossaries/{term_glossary_id}/terms/{term_id}", "type": "TARGET"}
        ]
    }
    response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def attach_term_to_column(project_id, entry_location_id, entry_dataset_name, entry_table_name, entry_column_name, term_project_id, term_location_id, term_glossary_id, term_id, entry_link_id):
    creds = get_credentials()
    project_number = get_project_number(project_id)
    term_project_number = get_project_number(term_project_id)
    entry_location_id = entry_location_id.lower()
    term_location_id = term_location_id.lower()
    url = f"https://dataplex.googleapis.com/v1/projects/{project_number}/locations/{entry_location_id}/entryGroups/@bigquery/entryLinks?entry_link_id={entry_link_id}"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {
        "entry_link_type": "projects/dataplex-types/locations/global/entryLinkTypes/definition",
        "entry_references": [
            {
                "name": f"projects/{project_number}/locations/{entry_location_id}/entryGroups/@bigquery/entries/bigquery.googleapis.com/projects/{project_id}/datasets/{entry_dataset_name}/tables/{entry_table_name}",
                "type": "SOURCE",
                "path": f"Schema.{entry_column_name}"
            },
            {
                "name": f"projects/{term_project_number}/locations/{term_location_id}/entryGroups/@dataplex/entries/projects/{term_project_number}/locations/{term_location_id}/glossaries/{term_glossary_id}/terms/{term_id}",
                "type": "TARGET"
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def create_synonym_link(term1_project_id, term1_location, term1_glossary_id, term1_id, term2_project_id, term2_location, term2_glossary_id, term2_id, entry_link_id):
    creds = get_credentials()
    term1_project_number = get_project_number(term1_project_id)
    term2_project_number = get_project_number(term2_project_id)
    url = f"https://dataplex.googleapis.com/v1/projects/{term1_project_id}/locations/{term1_location}/entryGroups/%40dataplex/entryLinks?entry_link_id={entry_link_id}"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {
        "entry_link_type": "projects/dataplex-types/locations/global/entryLinkTypes/synonym",
        "entry_references": [
            {"name": f"projects/{term1_project_number}/locations/{term1_location}/entryGroups/@dataplex/entries/projects/{term1_project_number}/locations/{term1_location}/glossaries/{term1_glossary_id}/terms/{term1_id}", "type": "UNSPECIFIED"},
            {"name": f"projects/{term2_project_number}/locations/{term2_location}/entryGroups/@dataplex/entries/projects/{term2_project_number}/locations/{term2_location}/glossaries/{term2_glossary_id}/terms/{term2_id}", "type": "UNSPECIFIED"}
        ]
    }
    response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)

def create_related_link(term1_project_id, term1_location, term1_glossary_id, term1_id, term2_project_id, term2_location, term2_glossary_id, term2_id, entry_link_id):
    creds = get_credentials()
    term1_project_number = get_project_number(term1_project_id)
    term2_project_number = get_project_number(term2_project_id)
    url = f"https://dataplex.googleapis.com/v1/projects/{term1_project_id}/locations/{term1_location}/entryGroups/%40dataplex/entryLinks?entry_link_id={entry_link_id}"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {
        "entry_link_type": "projects/dataplex-types/locations/global/entryLinkTypes/related",
        "entry_references": [
            {"name": f"projects/{term1_project_number}/locations/{term1_location}/entryGroups/@dataplex/entries/projects/{term1_project_number}/locations/{term1_location}/glossaries/{term1_glossary_id}/terms/{term1_id}", "type": "UNSPECIFIED"},
            {"name": f"projects/{term2_project_number}/locations/{term2_location}/entryGroups/@dataplex/entries/projects/{term2_project_number}/locations/{term2_location}/glossaries/{term2_glossary_id}/terms/{term2_id}", "type": "UNSPECIFIED"}
        ]
    }
    response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
    return handle_response(response)


# --- CLI Setup ---

def main():
    parser = argparse.ArgumentParser(description="Dataplex Business Glossary Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Glossary subcommands
    subparsers.add_parser("list-glossaries").add_argument("--project_id", required=True), subparsers.choices["list-glossaries"].add_argument("--location", required=True)
    
    p = subparsers.add_parser("create-glossary")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)
    p.add_argument("--display_name", required=True)
    p.add_argument("--description", required=True)

    subparsers.add_parser("get-glossary").add_argument("--project_id", required=True), subparsers.choices["get-glossary"].add_argument("--location", required=True), subparsers.choices["get-glossary"].add_argument("--glossary_id", required=True)

    p = subparsers.add_parser("add-glossary-overview")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)
    p.add_argument("--overview", required=True)

    # Category subcommands
    p = subparsers.add_parser("list-categories")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)

    p = subparsers.add_parser("create-category")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)
    p.add_argument("--category_id", required=True)
    p.add_argument("--display_name", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--parent_category_id")

    p = subparsers.add_parser("add-category-overview")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)
    p.add_argument("--category_id", required=True)
    p.add_argument("--overview", required=True)

    p = subparsers.add_parser("add-category-contacts")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)
    p.add_argument("--category_id", required=True)
    p.add_argument("--contact_name", required=True)
    p.add_argument("--contact_email", required=True)

    # Term subcommands
    p = subparsers.add_parser("list-terms")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)

    p = subparsers.add_parser("create-term")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)
    p.add_argument("--term_id", required=True)
    p.add_argument("--display_name", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--parent_category_id")

    p = subparsers.add_parser("add-term-overview")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)
    p.add_argument("--term_id", required=True)
    p.add_argument("--overview", required=True)

    p = subparsers.add_parser("add-term-contacts")
    p.add_argument("--project_id", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--glossary_id", required=True)
    p.add_argument("--term_id", required=True)
    p.add_argument("--contact_name", required=True)
    p.add_argument("--contact_email", required=True)

    # Linking subcommands
    p = subparsers.add_parser("attach-term-to-data-asset")
    p.add_argument("--project_id", required=True)
    p.add_argument("--entry_location_id", required=True)
    p.add_argument("--entry_group_id", required=True)
    p.add_argument("--entry_id", required=True)
    p.add_argument("--term_project_id", required=True)
    p.add_argument("--term_location_id", required=True)
    p.add_argument("--term_glossary_id", required=True)
    p.add_argument("--term_id", required=True)
    p.add_argument("--entry_link_id", required=True)

    p = subparsers.add_parser("attach-term-to-column")
    p.add_argument("--project_id", required=True)
    p.add_argument("--entry_location_id", required=True)
    p.add_argument("--entry_dataset_name", required=True)
    p.add_argument("--entry_table_name", required=True)
    p.add_argument("--entry_column_name", required=True)
    p.add_argument("--term_project_id", required=True)
    p.add_argument("--term_location_id", required=True)
    p.add_argument("--term_glossary_id", required=True)
    p.add_argument("--term_id", required=True)
    p.add_argument("--entry_link_id", required=True)

    p = subparsers.add_parser("create-synonym-link")
    p.add_argument("--term1_project_id", required=True)
    p.add_argument("--term1_location", required=True)
    p.add_argument("--term1_glossary_id", required=True)
    p.add_argument("--term1_id", required=True)
    p.add_argument("--term2_project_id", required=True)
    p.add_argument("--term2_location", required=True)
    p.add_argument("--term2_glossary_id", required=True)
    p.add_argument("--term2_id", required=True)
    p.add_argument("--entry_link_id", required=True)

    p = subparsers.add_parser("create-related-link")
    p.add_argument("--term1_project_id", required=True)
    p.add_argument("--term1_location", required=True)
    p.add_argument("--term1_glossary_id", required=True)
    p.add_argument("--term1_id", required=True)
    p.add_argument("--term2_project_id", required=True)
    p.add_argument("--term2_location", required=True)
    p.add_argument("--term2_glossary_id", required=True)
    p.add_argument("--term2_id", required=True)
    p.add_argument("--entry_link_id", required=True)


    args = parser.parse_args()

    if args.command == "list-glossaries":
        result = list_glossaries(args.project_id, args.location)
    elif args.command == "create-glossary":
        result = create_glossary(args.project_id, args.location, args.glossary_id, args.display_name, args.description)
    elif args.command == "get-glossary":
        result = get_glossary(args.project_id, args.location, args.glossary_id)
    elif args.command == "add-glossary-overview":
        result = add_glossary_overview(args.project_id, args.location, args.glossary_id, args.overview)
    elif args.command == "list-categories":
        result = list_categories(args.project_id, args.location, args.glossary_id)
    elif args.command == "create-category":
        result = create_category(args.project_id, args.location, args.glossary_id, args.category_id, args.display_name, args.description, args.parent_category_id)
    elif args.command == "add-category-overview":
        result = add_category_overview(args.project_id, args.location, args.glossary_id, args.category_id, args.overview)
    elif args.command == "add-category-contacts":
        result = add_category_contacts(args.project_id, args.location, args.glossary_id, args.category_id, args.contact_name, args.contact_email)
    elif args.command == "list-terms":
        result = list_terms(args.project_id, args.location, args.glossary_id)
    elif args.command == "create-term":
        result = create_term(args.project_id, args.location, args.glossary_id, args.term_id, args.display_name, args.description, args.parent_category_id)
    elif args.command == "add-term-overview":
        result = add_term_overview(args.project_id, args.location, args.glossary_id, args.term_id, args.overview)
    elif args.command == "add-term-contacts":
        result = add_term_contacts(args.project_id, args.location, args.glossary_id, args.term_id, args.contact_name, args.contact_email)
    elif args.command == "attach-term-to-data-asset":
        result = attach_term_to_data_asset(args.project_id, args.entry_location_id, args.entry_group_id, args.entry_id, args.term_project_id, args.term_location_id, args.term_glossary_id, args.term_id, args.entry_link_id)
    elif args.command == "attach-term-to-column":
        result = attach_term_to_column(args.project_id, args.entry_location_id, args.entry_dataset_name, args.entry_table_name, args.entry_column_name, args.term_project_id, args.term_location_id, args.term_glossary_id, args.term_id, args.entry_link_id)
    elif args.command == "create-synonym-link":
        result = create_synonym_link(args.term1_project_id, args.term1_location, args.term1_glossary_id, args.term1_id, args.term2_project_id, args.term2_location, args.term2_glossary_id, args.term2_id, args.entry_link_id)
    elif args.command == "create-related-link":
        result = create_related_link(args.term1_project_id, args.term1_location, args.term1_glossary_id, args.term1_id, args.term2_project_id, args.term2_location, args.term2_glossary_id, args.term2_id, args.entry_link_id)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
