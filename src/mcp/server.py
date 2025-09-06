from typing import Dict, Any
import logging
from mcp.server.fastmcp import FastMCP
from src.core.jira.jira_integration import *

# Configure logging to stderr
logging.basicConfig(level=logging.INFO)

# Initialize FastMCP server
mcp = FastMCP("jira-tools")

@mcp.tool()
def create_jira_issue(
    project: str,
    title: str,
    issue_type: str,
    description: str,
    parent: str = None,
    assignee_email: str = None,
    custom_fields: Dict[str, Any] = None
) -> str:
    """Create a Jira issue in a specific project and parent, with custom fields and rich text \
        description.

    Args:
        project: Project key
        title: Issue title
        issue_type: Type of issue
        description: Issue description
        parent: Parent issue key (optional)
        assignee_email: Assignee's email (optional)
        custom_fields: Custom fields (optional)
    """
    return create_jira_issue_impl(
        project=project,
        parent=parent,
        assignee_email=assignee_email,
        title=title,
        issue_type=issue_type,
        description=description,
        custom_fields=custom_fields or {}
    ).key

@mcp.tool()
def get_transitions(issue_key: str) -> Dict[str, str]:
    """Get all possible transitions for a Jira issue.
    
    Args:
        issue_key: The Jira issue key
    """
    return get_jira_transitions_impl(issue_key)

@mcp.tool()
def transition_issue(issue_key: str, transition_name: str) -> str:
    """Transition a Jira issue to a new status.
    
    Args:
        issue_key: The Jira issue key
        transition_name: Name of the transition
    """
    return transition_jira_issue_impl(issue_key, transition_name)

@mcp.tool()
def get_issue_info(issue_key: str) -> Dict[str, str]:
    """Get the title and description of a Jira issue.
    
    Args:
        issue_key: The Jira issue key
    """
    return get_issue_details_impl(issue_key)

@mcp.tool()
def get_issue_types() -> Dict[str, Dict[str, str]]:
    """Get all available issue types from Jira.
    
    Returns:
        A dictionary containing all available issue types with their details including:
        - name: The name of the issue type
        - id: The unique identifier
        - description: A description of the issue type
        - subtask: Whether this is a subtask type
        - icon_url: URL to the issue type's icon
    """
    return get_issue_types_impl()

if __name__ == "__main__":
    # Initialize and run the server using STDIO transport
    mcp.run(transport="stdio")
