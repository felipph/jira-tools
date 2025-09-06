from jira import JIRA
from langchain.tools import tool
from typing import Dict, Any
from core.jira.jira_integration import *


@tool("create_jira_issue_custom")
def create_jira_issue(
    project: str,
    parent: str,
    assignee_email: str,
    title: str,
    issue_type: str,
    description: str,
    custom_fields: Dict[str, Any]
) -> str:
    """Create a Jira issue in a specific project and parent, with custom fields and rich text description."""
    return create_jira_issue_impl(
        project=project,
        parent=parent,
        assignee_email=assignee_email,
        title=title,
        issue_type=issue_type,
        description=description,
        custom_fields=custom_fields
    )


@tool("get_jira_transitions")
def get_jira_transitions(issue_key: str) -> Dict[str, str]:
    """Get all possible transitions for a Jira issue."""
    return get_transitions_with_fields_impl(issue_key)



@tool("transition_jira_issue")
def transition_jira_issue(issue_key: str, transition_name: str) -> str:
    """Transition a Jira issue to a new status."""
    return transition_jira_issue_impl(issue_key, transition_name)



@tool("get_jira_issue_details")
def get_issue_details(issue_key: str) -> Dict[str, str]:
    """Get the title and description of a Jira issue for LLM context.
    Useful for understanding the content and context of an issue when generating text or making decisions."""
    return get_issue_details_impl(issue_key)
