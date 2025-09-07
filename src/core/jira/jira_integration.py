from jira import JIRA
from typing import Dict, Any, Optional
from functools import wraps
from dotenv import load_dotenv
from tempoapiclient import client_v4
from datetime import datetime
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
    """Create a Jira issue in a specific project and parent, with custom fields and rich text description.
    
    Args:
        project: The project key (e.g., 'PROJ')
        parent: The parent issue key (e.g., 'PROJ-123'). Can be None for top-level issues
        assignee_email: Email of the user to assign the issue to
        title: The summary/title of the issue
        issue_type: The name of the issue type (e.g., 'Task', 'Bug', 'Story')
        description: Rich text description supporting Jira wiki markup
        custom_fields: Dictionary of custom fields where:
            - Keys must be the field IDs (e.g., 'customfield_10001')
            - Values must match the expected format for each field type:
                * Single Select: {'value': 'option_value'} or 'option_value'
                * Multi Select: [{'value': 'option1'}, {'value': 'option2'}] or ['option1', 'option2']
                * User Picker: {'accountId': 'user_account_id'}
                * Date: '2023-09-06' (YYYY-MM-DD format)
                * DateTime: '2023-09-06T10:00:00.000+0000'
                * Number: Simple numeric value
                * Text: Simple string value
                * Labels: List of strings
                * Sprint: Sprint ID (number)
                * Epic Link: Issue key of the epic
            Example:
            {
                'customfield_10001': {'value': 'High'},  # Single select
                'customfield_10002': [{'value': 'Tag1'}, {'value': 'Tag2'}],  # Multi select
                'customfield_10003': '2023-09-06',  # Date
                'customfield_10004': 42,  # Number
                'customfield_10005': {'accountId': 'user123'}  # User picker
            }
            
    Returns:
        The created issue object
        
    Raises:
        ValueError: If assignee email is not found or if custom field values are incorrectly formatted
    """

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
def get_transitions_with_fields_impl(issue_key: str) -> Dict[str, Dict[str, Any]]:
    """Get all possible transitions and their required fields for a Jira issue.
    
    Args:
        issue_key: The key of the issue to get transitions for (e.g., 'PROJ-123')
    
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
    """
    transitions = jira_client.transitions(issue_key, expand='transitions.fields')
    
    result = {}
    for transition in transitions:
        # Get required fields for this transition
        required_fields = {}
        if 'fields' in transition:
            for field_id, field_data in transition['fields'].items():
                # if field_data.get('required', False):
                field_name = field_data.get('name', field_id)
                field_schema = field_data.get('schema', {})
                field_type = field_schema.get('type', 'string')
                
                required_fields[field_id] = {
                    'name': field_name,
                    'type': field_type,
                    'allowedValues': field_data.get('allowedValues', []),
                    'description': field_data.get('description', '')
                }
    
        result[transition['name']] = {
            'id': transition['id'],
            'required_fields': required_fields
        }
    
    return result

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
def get_issue_details_impl(issue_key: str) -> Dict[str, Any]:
    """Get detailed information about a Jira issue including subtasks and custom fields.
    
    Args:
        issue_key: The key of the issue to get details for (e.g., 'PROJ-123')
    
    Returns:
        A dictionary containing the issue's details including:
        - Basic information (title, description, type, status)
        - Parent information if it exists
        - List of subtasks with their details if they exist
        - All filled custom fields
    """
    # Get issue with subtasks
    issue = jira_client.issue(issue_key, expand='subtasks')
    
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
    
    # Handle subtasks
    subtasks = []
    if hasattr(issue.fields, 'subtasks'):
        for subtask in issue.fields.subtasks:
            # Get full subtask details
            full_subtask = jira_client.issue(subtask.key)
            subtask_description = getattr(full_subtask.fields, 'description', None)
            if not subtask_description or subtask_description.strip() == '':
                subtask_description = "Sem Descrição"
                
            subtasks.append({
                'key': subtask.key,
                'title': full_subtask.fields.summary,
                'description': subtask_description,
                'status': full_subtask.fields.status.name,
                'issue_type': full_subtask.fields.issuetype.name,
                'assignee': getattr(full_subtask.fields.assignee, 'displayName', 'Unassigned'),
                'priority': getattr(full_subtask.fields.priority, 'name', 'No Priority')
            })

    # Extract custom fields with only essential information (ID, KEY, NAME, VALUE)
    custom_fields = {}
    field_meta = {}
    
    # Get field metadata if available
    project = issue.fields.project.key
    issue_type = issue.fields.issuetype.name
    try:
        create_meta = jira_client.createmeta(
            projectKeys=project,
            issuetypeNames=issue_type,
            expand='projects.issuetypes.fields'
        )
        if create_meta['projects'] and create_meta['projects'][0]['issuetypes']:
            field_meta = create_meta['projects'][0]['issuetypes'][0].get('fields', {})
    except Exception:
        # Continue without metadata if we can't fetch it
        pass

    for field_name, field_value in issue.raw['fields'].items():
        if field_name.startswith('customfield_') and field_value is not None:
            field_info = field_meta.get(field_name, {})
            
            # Extract the actual value from different field types
            actual_value = field_value
            if isinstance(field_value, dict):
                if 'value' in field_value:
                    actual_value = field_value['value']
                elif 'name' in field_value:
                    actual_value = field_value['name']
                # Keep ID if it exists
                if 'id' in field_value:
                    actual_value = {'id': field_value['id'], 'value': actual_value}
            elif isinstance(field_value, list):
                processed_values = []
                for item in field_value:
                    if isinstance(item, dict):
                        item_value = item.get('value', item.get('name', None))
                        if item_value:
                            if 'id' in item:
                                processed_values.append({'id': item['id'], 'value': item_value})
                            else:
                                processed_values.append(item_value)
                    else:
                        processed_values.append(item)
                actual_value = processed_values if processed_values else field_value

            custom_fields[field_name] = {
                'id': field_name.split('_')[1] if '_' in field_name else field_name,
                'key': field_name,
                'name': field_info.get('name', field_name),
                'value': actual_value
            }
    
    return {
        'key': issue.key,
        'title': issue.fields.summary,
        'description': description,
        'issue_type': issue.fields.issuetype.name,
        'status': issue.fields.status.name,
        'project': issue.fields.project.key,
        'parent': parent_info,
        'assignee': getattr(issue.fields.assignee, 'displayName', 'Unassigned'),
        'priority': getattr(issue.fields.priority, 'name', 'No Priority'),
        'created': str(issue.fields.created),
        'updated': str(issue.fields.updated),
        'subtasks': subtasks,
        'subtasks_count': len(subtasks),
        'custom_fields': custom_fields
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

def _extract_required_fields(transition_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Helper function to extract required fields from transition data.
    
    Args:
        transition_data: The transition data from Jira API
        
    Returns:
        Dictionary of required fields with their details
    """
    required_fields = {}
    if 'fields' in transition_data:
        for field_id, field_data in transition_data['fields'].items():
            if field_data.get('required', False):
                field_name = field_data.get('name', field_id)
                field_schema = field_data.get('schema', {})
                field_type = field_schema.get('type', 'string')
                required_fields[field_id] = {
                    'name': field_name,
                    'type': field_type,
                    'allowedValues': field_data.get('allowedValues', []),
                    'description': field_data.get('description', ''),
                }
    return required_fields

@with_jira_client
def get_issue_type_custom_fields_by_project_impl(project_key: str, issue_type_name: str) -> str:
    """Get a structured text description of all fields available for a specific issue type.
    
    Args:
        project_key: The project key (e.g., 'PROJ')
        issue_type_name: The name of the issue type (e.g., 'Task', 'Bug')
        
    Returns:
        A formatted string containing all field information organized by categories
    """
    # Get project and issue type info
    project = jira_client.project(project_key)
    create_meta = jira_client.createmeta(
        projectIds=[project.id],
        expand='projects.issuetypes.fields'
    )
    
    # Find the specific issue type
    issue_type_meta = None
    for project_meta in create_meta['projects']:
        for issuetype in project_meta['issuetypes']:
            if issuetype['name'].lower() == issue_type_name.lower():
                issue_type_meta = issuetype
                break
        if issue_type_meta:
            break
    
    if not issue_type_meta:
        raise ValueError(f"Issue type '{issue_type_name}' not found in project '{project_key}'")
    
    fields = issue_type_meta['fields']
    
    # Organize fields by category
    categories = {
        'Required Fields': [],
        'Custom Fields': [],
        'Standard Fields': []
    }
    
    for field_id, field_info in fields.items():
        # Create field description
        field_desc = {
            'name': field_info['name'],
            'id': field_id,
            'type': field_info.get('schema', {}).get('type', 'unknown'),
            'required': field_info.get('required', False),
            'custom': field_id.startswith('customfield_')
        }
        
        # Add allowed values if they exist
        if 'allowedValues' in field_info:
            values = []
            for val in field_info['allowedValues']:
                if 'value' in val:
                    values.append(val['value'])
                elif 'name' in val:
                    values.append(val['name'])
            if values:
                field_desc['allowed_values'] = values
        
        # Categorize the field
        if field_desc['required']:
            categories['Required Fields'].append(field_desc)
        elif field_desc['custom']:
            categories['Custom Fields'].append(field_desc)
        else:
            categories['Standard Fields'].append(field_desc)
    
    # Format the output
    output = []
    output.append(f"Fields for {issue_type_name} in {project_key}")
    output.append("=" * 50)
    
    for category, fields in categories.items():
        if fields:
            output.append(f"\n{category}:")
            output.append("-" * len(category))
            
            for field in sorted(fields, key=lambda x: x['name']):
                output.append(f"\n{field['name']} ({field['id']})")
                output.append(f"Type: {field['type']}")
                if field.get('allowed_values'):
                    output.append("Allowed values: " + ", ".join(field['allowed_values']))
                if field['required']:
                    output.append("* Required field")
                output.append("")
    
    return "\n".join(output)

# Global Tempo client instance
tempo_client = None

def init_tempo_client() -> None:
    """Initialize the Tempo client."""
    global tempo_client
    tempo_api_key = os.getenv("TEMPO_API_KEY")
    if not tempo_api_key:
        raise ValueError("TEMPO_API_KEY environment variable is not set.")
    tempo_client = client_v4.Tempo(auth_token=tempo_api_key)

def with_tempo_client(func):
    """Decorator to ensure Tempo client is initialized."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if tempo_client is None:
            init_tempo_client()
        return func(*args, **kwargs)
    return wrapper

@with_jira_client
@with_tempo_client
def register_worklog_tempo(
    issue_key: str, 
    assignee_email: str, 
    start_time: str, 
    time_in_seconds: int, 
    account_key: str, 
    description: str = "Atividade da tarefa", 
    task_date: str = datetime.now().strftime("%Y-%m-%d")
) -> str:
    """Register time tracking integration with Tempo.
    
    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')
        assignee_email: Email of the user who performed the work
        start_time: Time when the work started in "HH:MM:SS" format
        time_in_seconds: Duration of the work in seconds
        account_key: Tempo account key for time tracking
        description: Optional work description
        task_date: The date of the work in YYYY-MM-DD format
        
    Returns:
        Success or error message
        
    Raises:
        ValueError: If user not found or issue doesn't exist
    """
    # Search for the user by email
    users = jira_client.search_users(query=assignee_email)
    if not users:
        raise ValueError(f"No user found with email: {assignee_email}")
    
    assignee_account_id = users[0].accountId
    
    # Validate issue exists and get its ID
    issue = jira_client.issue(issue_key)
    if not issue:
        raise ValueError(f"No issue found with key: {issue_key}")
    
    try:
        # Create worklog using Tempo API client
        worklog = tempo_client.create_worklog(
            issueId=issue.id,
            timeSpentSeconds=time_in_seconds,
            dateFrom=task_date,
            startTime=start_time,
            description=description,
            accountId=assignee_account_id,
            attributes=[{"key": "_Account_", "value": account_key}]
        )
        return "✅ Worklog created successfully!"
    except Exception as e:
        return f"❌ Failed to create worklog: {str(e)}"

@with_tempo_client
def get_accounts_for_tempo() -> str:
    """Get all active accounts from Tempo.
    
    Returns:
        Formatted string with account information
        
    Raises:
        ValueError: If Tempo API key is not configured
    """
    try:
        # Get accounts using Tempo API client
        accounts = tempo_client.get_accounts()
        
        # Filter active accounts and format output
        data = ""
        for account in accounts:
            if account.get("status") == "OPEN":
                data += f"- Account Key: {account.get('key')}, Account Name: {account.get('name')}\n"
        
        return data if data else "No active accounts found"
    except Exception as e:
        return f"Error fetching accounts: {str(e)}"

if __name__ == "__main__":
    # Example usage of Tempo integration
    
    # Get all Tempo accounts
    accounts = get_accounts_for_tempo()
    print("Available Tempo accounts:")
    print(accounts)
    
    # Example: Register work log
    worklog = register_worklog_tempo(
        issue_key="ARQPERF-4676",
        assignee_email=os.getenv("JIRA_ACCOUNT_EMAIL"),
        start_time="09:00:00",
        time_in_seconds=300,  # 5 minutes
        account_key="PRJ-R2C3-MODERN-AWS",
        description="Example work log entry"
    )
    print("\nWorklog registration result:")
    print(worklog)

    # # print(createmeta)