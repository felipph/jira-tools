from jira import JIRA
from langchain.tools import tool
from typing import Dict, Any, Optional
from functools import wraps
from dotenv import load_dotenv
import os

load_dotenv()


# Global JIRA client instance
jira_client: Optional[JIRA] = None

def with_jira_client(func):
    """Decorator to ensure JIRA client is initialized."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if jira_client is None:
            init_jira_client()
        return func(*args, **kwargs)
    return wrapper

def init_jira_client() -> None:
    """Initialize the global JIRA client."""
    global jira_client
    jira_client = JIRA(server=os.environ["JIRA_URL"], 
        basic_auth=(
            os.environ["JIRA_ACCOUNT_EMAIL"], 
            os.environ["JIRA_API_TOKEN"])
        )


@with_jira_client
def create_jira_issue_impl(
    project: str,   
    parent: str,
    assignee_email: str,
    title: str,
    issue_type: str,
    description: str,
    custom_fields: Dict[str, Any]
) -> str:
    """Create a Jira issue in a specific project and parent, with custom fields and rich text description."""

    # Search for the user by email
    users = jira_client.search_users(query=assignee_email)
    if users:
        assignee_account_id = users[0].accountId
        print(f"Found user: {users[0].displayName} with accountId: {assignee_account_id}")
    else:
        raise ValueError(f"No user found with email: {assignee_email}")
    
    fields = {
        'project': {'key': project},
        'summary': title,
        'issuetype': {'name': issue_type},
        'description': description,  # Jira supports rich text (wiki markup)
        'parent': {'key': parent} if parent else None,
        'assignee': {'accountId': assignee_account_id},
    }
    # Add custom fields
    if custom_fields:
        fields.update(custom_fields)
    # Remove None values
    fields = {k: v for k, v in fields.items() if v is not None}
    return jira_client.create_issue(fields=fields)
    

@with_jira_client
def get_jira_transitions_impl(issue_key: str) -> Dict[str, str]:
    """Get all possible transitions for a Jira issue.
    
    Args:
        issue_key: The key of the issue to get transitions for (e.g., 'PROJ-123')
    
    Returns:
        A dictionary mapping transition names to their IDs
    """
    transitions = jira_client.transitions(issue_key)
    return {t['name']: t['id'] for t in transitions}

@with_jira_client
def transition_jira_issue_impl(issue_key: str, transition_name: str) -> str:
    """Transition a Jira issue to a new status.
    
    Args:
        issue_key: The key of the issue to transition (e.g., 'PROJ-123')
        transition_name: The name of the transition to perform (e.g., 'In Progress')
    
    Returns:
        A message indicating the result of the transition
    """
    # Get all available transitions
    transitions = jira_client.transitions(issue_key)
    
    # Find the transition ID by name
    transition_id = None
    for t in transitions:
        if t['name'].lower() == transition_name.lower():
            transition_id = t['id']
            break
    
    if transition_id is None:
        available_transitions = ", ".join(t['name'] for t in transitions)
        raise ValueError(f"Transition '{transition_name}' not found. Available transitions: {available_transitions}")
    
    # Perform the transition
    jira_client.transition_issue(issue_key, transition_id)
    return f"Successfully transitioned {issue_key} using transition '{transition_name}'"
@with_jira_client
def get_issue_details_impl(issue_key: str) -> Dict[str, str]:
    """Get the title (summary) and description of a Jira issue.
    
    Args:
        issue_key: The key of the issue to get details for (e.g., 'PROJ-123')
    
    Returns:
        A dictionary containing the issue's summary and description
    """
    issue = jira_client.issue(issue_key)
    
    # Handle description - return "Sem Descrição" if None or empty
    description = getattr(issue.fields, 'description', None)
    if not description or description.strip() == '':
        description = "Sem Descrição"
    
    # Handle parent - check if parent exists and format accordingly
    parent = getattr(issue.fields, 'parent', None)
    if parent:
        parent_summary = parent.raw.get('fields', {}).get('summary', '')
        parent_info = f"{parent.key} - {parent_summary}"
    else:
        parent_info = "No Parent"
    
    return {
        'title': issue.fields.summary,
        'description': description,
        'issue_type': issue.fields.issuetype.name,
        'status': issue.fields.status.name,
        'project': issue.fields.project.key,
        'parent': parent_info,
    }




@with_jira_client
def get_issue_types_impl() -> Dict[str, Dict[str, str]]:
    """Get all available issue types from Jira.
    
    Returns:
        A dictionary containing issue types with their details:
        {
            "type_name": {
                "id": "id of the type",
                "description": "type description",
                "subtask": boolean indicating if it's a subtask type,
                "icon_url": "URL to the type's icon"
            }
        }
    """
    issue_types = jira_client.issue_types()
    return {
        issue_type.name: {
            "id": issue_type.id,
            "description": issue_type.description or "No description available",
            "subtask": issue_type.subtask,
            "icon_url": issue_type.iconUrl
        }
        for issue_type in issue_types
    }
if __name__ == "__main__":
    from src.core.jira.jira_integration import (
        create_jira_issue_impl, transition_jira_issue_impl, get_issue_details_impl
    )
    
    result = create_jira_issue_impl(
        project="PROJ-XXX",
        parent="PROJ-2463",
        title="Test Issue",
        assignee_email=""
    )