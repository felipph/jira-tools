
from typing import Dict, Any
import logging
from mcp.server.fastmcp import FastMCP
from src.core.jira.jira_integration import *

# Configure logging to stderr
logging.basicConfig(level=logging.INFO)

# Initialize FastMCP server
mcp = FastMCP("jira-tools")

@mcp.tool()
def get_last_comments(issue_key: str, n: int = 5) -> Any:
    """
    Get the last N comments of a Jira card/issue.
    Args:
        issue_key: The key of the Jira card/issue (e.g., 'PROJ-123')
        n: Number of last comments to retrieve (default: 5)
    Returns:
        List of comments (each as dict with author, created, body)
    """
    return get_last_comments_impl(issue_key, n)

@mcp.tool()
def add_comment_to_card(issue_key: str, comment_markdown: str) -> str:
    """
    Add a comment to a Jira card/issue. Accepts markdown format for the comment.
    Args:
        issue_key: The key of the Jira card/issue (e.g., 'PROJ-123')
        comment_markdown: The comment in markdown format
    Returns:
        Success message or error
    """
    return add_comment_to_issue_impl(issue_key, comment_markdown)


@mcp.tool()
def create_jira_issue(
    project: str,
    parent: str,
    assignee_email: str,
    title: str,
    issue_type: str,
    description: str,
    estrutura: str,
    tipo_demanda: str,
    account: int,
    processo: str,
    cip_team: str,
    start_date: str,
    origem_demanda: str,
    alinhamento: str,
    quarter: str,
    sprint_prevista: str
) -> str:
    """
    Create a Jira issue with the given parameters and return the issue key.

    Args:
        project: The project key (e.g., 'PROJ')
        parent: Parent issue key (e.g., 'PROJ-123') for sub-tasks or issues in hierarchy
        assignee_email: Email address of the user to assign the issue to
        title: Summary/title of the issue
        issue_type: Type of the issue (e.g., 'Tarefa', 'Subtarefa')
        description: Issue description with Jira wiki markup support
        estrutura: Estrutura value (field: customfield_10310) you can use get_issue_type_fields to see available options
        tipo_demanda: Tipo de Demanda value (field: customfield_10311) you can use get_issue_type_fields to see available options
        account: Account ID (int) (field: customfield_10058) you can use get_issue_type_fields to see available options
        processo: Processo value (field: customfield_10312) you can use get_issue_type_fields to see available options
        cip_team: CIP Team value (field: customfield_10136) you can use get_issue_type_fields to see available options
        start_date: Start date in YYYY-MM-DD format (field: customfield_10015) you can use get_issue_type_fields to see available options
        origem_demanda: Origem da Demanda value (field: customfield_10339) you can use get_issue_type_fields to see available options
        alinhamento: Alinhamento value (field: customfield_10307) you can use get_issue_type_fields to see available options
        quarter: Quarter value (field: customfield_10308) you can use get_issue_type_fields to see available options
        sprint_prevista: Sprint Prevista value (field: customfield_10309) you can use get_issue_type_fields to see available options

    Returns:
        The key of the created issue (e.g., 'PROJ-123')
    """
    return criar_tarefa_jira(
        project=project,
        parent=parent,
        assignee_email=assignee_email,
        title=title,
        issue_type=issue_type,
        description=description,
        estrutura=estrutura,
        tipo_demanda=tipo_demanda,
        account=account,
        processo=processo,
        cip_team=cip_team,
        start_date=start_date,
        origem_demanda=origem_demanda,
        alinhamento=alinhamento,
        quarter=quarter,
        sprint_prevista=sprint_prevista
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
def get_issue_types() -> Any:
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
def get_issue_type_fields(project_key: str, issue_type_name: str, field: str = None) -> str:
    """Get a detailed description of all fields available for a specific kind of issue type in a project.
    
    This tool provides a structured list of all fields that can be used
    when creating or editing issues of a specific type. Fields are organized into categories
    (Required, Custom, and Standard) and include information about field types and allowed values.
    
    Args:
        project_key: The project key (e.g., 'ARQPERF')
        issue_type_name: The name of the issue type (e.g., 'Tarefa')
        field: Optional specific field name to filter the results (e.g., 'summary', 'issuetype')
    
    Returns:
        A JSON string containing a list of fields with their details:
        [
            {
                "field": "summary",
                "name": "Resumo",
                "schema": "string",
                "allowedValues": []
            },
            {
                "field": "issuetype",
                "name": "Tipo de item",
                "schema": "issuetype",
                "allowedValues": [
                {
                    "id": "10045",
                    "name": "Tarefa"
                }
        ]
    """
    return get_issue_type_custom_fields_by_project_impl(project_key, issue_type_name, field)

@mcp.tool()
def get_tempo_accounts() -> str:
    """Get all available Tempo accounts.
    
    This tool retrieves a list of all active Tempo accounts that can be used for time tracking.
    Each account entry includes both the account key (used for logging time) and its display name.
    
    Returns:
        A formatted string containing all active Tempo accounts, with each line showing:
        - Account Key: The unique identifier used when logging time
        - Account Name: The human-readable name of the account
        
    Example response:
        - Account Key: PROJ-MAIN, Account Name: Main Project
        - Account Key: PROJ-DEV, Account Name: Development
        - Account Key: PROJ-SUPPORT, Account Name: Customer Support
        
    Raises:
        ValueError: If Tempo API environment variables are not configured properly
    """
    return get_accounts_for_tempo()

@mcp.tool()
def log_time_spent_in_issue(
    issue_key: str,
    assignee_email: str,
    start_time: str,
    time_in_seconds: int,
    account_key: str,
    description: str = "Atividade da tarefa",
    task_date: str = None
) -> str:
    """Log the time spent on an issue in a Jira issue.
    
    This tool allows you to log work time against a Jira issue for time tracking.
    
    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')
        assignee_email: Email of the user who performed the work
        start_time: Time when the work started in "HH:MM:SS" format (e.g., "09:00:00")
        time_in_seconds: Duration of the work in seconds (e.g., 3600 for 1 hour)
        account_key: The Tempo account key to log time against (use get_tempo_accounts to see available accounts)
        description: Optional description of the work performed (defaults to "Atividade da tarefa")
        task_date: Optional date for the worklog in "YYYY-MM-DD" format (defaults to current date)
    
    Returns:
        A message indicating success or failure of the worklog creation
        
    Example Usage:
        status = log_time_spent_in_issue(
            issue_key="PROJ-123",
            assignee_email="user@company.com",
            start_time="09:00:00",
            time_in_seconds=3600,  # 1 hour
            account_key="PROJ-DEV",
            description="Implementing new feature",
            task_date="2025-09-07"  # Optional, defaults to today
        )
        
    Raises:
        ValueError: If user email is not found, issue doesn't exist, or Tempo configuration is missing
    """
    return register_worklog_tempo(
        issue_key=issue_key,
        assignee_email=assignee_email,
        start_time=start_time,
        time_in_seconds=time_in_seconds,
        account_key=account_key,
        description=description,
        task_date=task_date
    )

@mcp.tool()
def get_current_date() -> str:
    """Get the current date in YYYY-MM-DD format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

@mcp.tool()
def get_tarefa_creation_guide() -> str:
    """Get detailed instructions for creating a Jira task.
    
    This tool provides a comprehensive guide on how to create a task in Jira,
    including all required fields and their formats.
    
    Returns:
        A formatted string containing detailed instructions on how to create
        a task, including required fields, custom fields, and their formats.
    """
    return get_instructions_to_create_tarefa()

@mcp.tool()
def get_subtarefa_creation_guide() -> str:
    """Get detailed instructions for creating a Jira subtask.
    
    This tool provides a comprehensive guide on how to create a subtask in Jira,
    including all required fields and their formats.
    
    Returns:
        A formatted string containing detailed instructions on how to create
        a subtask, including required fields, custom fields, and their formats.
    """
    return get_instructions_to_create_subtarefa()


@mcp.tool()
def get_child_issues_by_parent(parent_key: str) -> Dict[str, Any]:
    """Get all issues that have the specified issue as their parent.
    
    Args:
        parent_key: The key of the parent issue (e.g., 'PROJ-123')
    
    Returns:
        A dictionary containing:
        - parent_info: Basic information about the parent issue
        - children: List of child issues with their details
        - total_children: Count of child issues
    """
    return get_child_issues_by_parent_impl(parent_key)


if __name__ == "__main__":
    # Initialize and run the server using STDIO transport
    mcp.run(transport="stdio")
