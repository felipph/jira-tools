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
    """Create a Jira issue with support for custom fields and rich text description.

    Use this tool to create new issues in Jira. The description supports Jira wiki markup for rich text
    formatting. Custom fields must be properly formatted according to their field types.
    
    You can use the get_issue_type_fields tool first to see what fields are available and their formats
    for a specific project and issue type.

    Args:
        project: The project key (e.g., 'PROJ')
        title: Summary/title of the issue
        issue_type: Type of the issue (e.g., 'Task', 'Bug', 'Story')
        description: Issue description with Jira wiki markup support
        parent: Parent issue key (e.g., 'PROJ-123') for sub-tasks or issues in hierarchy
        assignee_email: Email address of the user to assign the issue to
        custom_fields: Dictionary of custom fields where the key is the field ID and value follows the field type format:
            Field Type Formats:
            - Single Select: {'value': 'option_value'} or just 'option_value'
            - Multi Select: [{'value': 'option1'}, {'value': 'option2'}] or ['option1', 'option2']
            - User Picker: {'accountId': 'user_account_id'}
            - Date: 'YYYY-MM-DD' (e.g., '2025-09-06')
            - DateTime: 'YYYY-MM-DDThh:mm:ss.sss+0000'
            - Number: Simple numeric value
            - Text: Simple string value
            - Labels: List of strings
            - Sprint: Sprint ID number
            - Epic Link: Epic issue key

            Example:
            {
                'customfield_10001': {'value': 'High'},  # Single select
                'customfield_10002': ['Tag1', 'Tag2'],  # Multi select
                'customfield_10003': '2025-09-06',  # Date
                'customfield_10004': 42,  # Number
                'customfield_10005': {'accountId': 'user123'}  # User picker
            }

    Returns:
        The key of the created issue (e.g., 'PROJ-123')

    Example Usage:
        issue_key = create_jira_issue(
            project='PROJ',
            title='Implement new feature',
            issue_type='Task',
            description='h2. Overview\n\nImplement the new feature',
            assignee_email='developer@company.com',
            custom_fields={
                'customfield_10001': {'value': 'High'},
                'customfield_10002': ['Frontend', 'UX']
            }
        )
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
def get_transitions(issue_key: str) -> Dict[str, Dict[str, Any]]:
    """Get all possible transitions and their required fields for a Jira issue.
    
    This tool provides detailed information about each available transition,
    including any mandatory fields that must be filled when making the transition.
    
    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')
    
    Returns:
        A dictionary containing transitions with their details:
        {
            "transition_name": {
                "id": "transition ID",
                "required_fields": {
                    "field_id": {
                        "name": "Field Name",
                        "type": "field type (string, array, etc)",
                        "allowedValues": [list of allowed values if any],
                        "description": "field description"
                    }
                }
            }
        }
    
    Example response:
        {
            "In Progress": {
                "id": "11",
                "required_fields": {}  # No required fields
            },
            "Resolved": {
                "id": "5",
                "required_fields": {
                    "resolution": {
                        "name": "Resolution",
                        "type": "resolution",
                        "allowedValues": ["Done", "Won't Fix", "Cannot Reproduce"],
                        "description": "How was this issue resolved?"
                    }
                }
            }
        }
    """
    return get_transitions_with_fields_impl(issue_key)

@mcp.tool()
def transition_issue(issue_key: str, transition_name: str) -> str:
    """Transition a Jira issue to a new status.
    
    Args:
        issue_key: The Jira issue key
        transition_name: Name of the transition
    """
    return transition_jira_issue_impl(issue_key, transition_name)

@mcp.tool()
def get_issue_info(issue_key: str) -> Dict[str, Any]:
    """Get comprehensive information about a Jira issue including its subtasks.
    
    This tool provides detailed information about an issue, including its basic details,
    parent relationship, and all subtasks if they exist.
    
    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')
    
    Returns:
        A dictionary containing comprehensive issue details including:
        - key: The issue key
        - title: Issue summary/title
        - description: Full description (or "Sem Descrição" if empty)
        - issue_type: Type of the issue
        - status: Current status
        - project: Project key
        - parent: Parent issue info (or "No Parent")
        - assignee: Assigned user name (or "Unassigned")
        - priority: Issue priority (or "No Priority")
        - created: Creation timestamp
        - updated: Last update timestamp
        - subtasks: List of subtask details including:
            - key: Subtask key
            - title: Subtask summary
            - description: Subtask description
            - status: Subtask status
            - issue_type: Type of subtask
            - assignee: Subtask assignee
            - priority: Subtask priority
        - subtasks_count: Number of subtasks
    
    Example response:
        {
            "key": "PROJ-123",
            "title": "Main Task",
            "description": "Main task description",
            "issue_type": "Task",
            "status": "In Progress",
            "project": "PROJ",
            "parent": "No Parent",
            "assignee": "John Doe",
            "priority": "High",
            "created": "2025-09-06T10:00:00.000+0000",
            "updated": "2025-09-06T11:00:00.000+0000",
            "subtasks": [
                {
                    "key": "PROJ-124",
                    "title": "Subtask 1",
                    "description": "Subtask description",
                    "status": "To Do",
                    "issue_type": "Sub-task",
                    "assignee": "Jane Smith",
                    "priority": "Medium"
                }
            ],
            "subtasks_count": 1
        }
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

@mcp.tool()
def get_issue_type_fields(project_key: str, issue_type_name: str) -> str:
    """Get a detailed description of all fields available for a specific kind of issue type in a project.
    
    This tool provides a structured list of all fields that can be used
    when creating or editing issues of a specific type. Fields are organized into categories
    (Required, Custom, and Standard) and include information about field types and allowed values.
    
    Args:
        project_key: The project key (e.g., 'PROJ')
        issue_type_name: The name of the issue type (e.g., 'Task', 'Bug')
    
    Returns:
        A formatted string containing all field information organized by categories.
        Example:
        
        Fields for Task in PROJ
        =======================
        
        Required Fields:
        --------------
        Summary (summary)
        Type: string
        * Required field
        
        Project (project)
        Type: project
        * Required field
        
        Custom Fields:
        ------------
        Department (customfield_10052)
        Type: option
        Allowed values: Engineering, Marketing, Sales
        
        Sprint (customfield_10011)
        Type: array
        
        Standard Fields:
        --------------
        Description (description)
        Type: string
        
        Priority (priority)
        Type: option
        Allowed values: Highest, High, Medium, Low, Lowest
    """
    return get_issue_type_custom_fields_by_project_impl(project_key, issue_type_name)


if __name__ == "__main__":
    # Initialize and run the server using STDIO transport
    mcp.run(transport="stdio")
