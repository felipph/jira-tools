from jira import JIRA
from typing import Dict, Any, Optional
from functools import wraps
from dotenv import load_dotenv
from tempoapiclient import client_v4
from datetime import datetime
import os
import json

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
def get_last_comments_impl(issue_key: str, n: int = 5) -> Any:
    """
    Get the last N comments of a Jira issue/card.
    Args:
        issue_key: The key of the Jira issue/card (e.g., 'PROJ-123')
        n: Number of last comments to retrieve (default: 5)
    Returns:
        List of comments (each as dict with author, created, body)
    """
    try:
        issue = jira_client.issue(issue_key)
        comments = issue.fields.comment.comments if hasattr(issue.fields, 'comment') else []
        last_comments = comments[-n:] if n > 0 else comments
        return [
            {
                'author': c.author.displayName,
                'created': c.created,
                'body': c.body
            } for c in last_comments
        ]
    except Exception as e:
        return f"❌ Failed to get comments: {str(e)}"


@with_jira_client
def add_comment_to_issue_impl(issue_key: str, comment_markdown: str) -> str:
    """
    Add a comment to a Jira issue/card. Accepts markdown and converts to Jira wiki markup.
    Args:
        issue_key: The key of the Jira issue/card (e.g., 'PROJ-123')
        comment_markdown: The comment in markdown format
    Returns:
        Success message or error
    """
    # Optionally, convert markdown to Jira wiki markup if needed
    # For now, just post as is (Jira supports some markdown, but wiki markup is preferred)
    try:
        jira_client.add_comment(issue_key, comment_markdown)
        return f"✅ Comment added to {issue_key}"
    except Exception as e:
        return f"❌ Failed to add comment: {str(e)}"


@with_jira_client
def criar_tarefa_jira(
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

    customfield_10310 (Estrutura): Must be one of the predefined values
    customfield_10311 (Tipo de Demanda (ARQPERF)): Must be one of the predefined values
    customfield_10058 (Account): Must be one of the predefined values. Must be the ID of the account, not the name
    customfield_10312 (Processo): Must be one of the predefined values
    customfield_10136 (CIP Team): Must be one of the predefined values
    customfield_10015 (Start Date): Must be a valid date in YYYY-MM-DD format
    customfield_10339 (Origem da Demanda): Always
    customfield_10307 (Alinhamento) : Try to figure out based on context
    customfield_10308 (Quarter): Is the quarter
    customfield_10309 (Sprint Prevista) : Must
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
        'customfield_10310':{'value': estrutura},
        'customfield_10311':{'value': tipo_demanda},
        'customfield_10058': account,
        'customfield_10312':{'value': processo},
        'customfield_10136':{'key': cip_team},
        'customfield_10015':start_date,
        'customfield_10339':{'value': origem_demanda},
        'customfield_10307':{'value': alinhamento},
        'customfield_10308':{'value': quarter},
        'customfield_10309':{'value': sprint_prevista}, 
    }

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
    issue = jira_client.issue(issue_key, expand='subtasks,issuelinks')
    
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


@with_jira_client
def get_issue_type_custom_fields_by_project_impl(project_key: str, issue_type_name: str, field: str = None) -> Dict[str, Any]:
    """Get a structured text description of all fields available for a specific issue type.
    
    Args:
        project_key: The project key (e.g., 'PROJ')
        issue_type_name: The name of the issue type (e.g., 'Task', 'Bug')
        field: Optional specific field ID to filter (e.g., 'customfield_10001'). Usefull to get the allowed values of a specific field.
        
    Returns:
        A json string containing all field information organized by categories
    """
    
    campos_ignorar = ['fixVersions','attachment']
    data = jira_client.createmeta(projectKeys='ARQPERF', issuetypeNames="Tarefa", expand="projects.issuetypes.fields")
    campos = []
    for campo in data.get('projects')[0].get('issuetypes')[0].get('fields'):
        if(campos_ignorar.__contains__(campo)):
            continue
        item = {            
            "field": campo,
            "name": data.get('projects')[0].get('issuetypes')[0].get('fields').get(campo).get('name'),
            "schema": data.get('projects')[0].get('issuetypes')[0].get('fields').get(campo).get('schema').get("type")               
        }
        valores_permitidos = []
        for allowed_value in data.get('projects')[0].get('issuetypes')[0].get('fields').get(campo).get('allowedValues',[]):
            valor_permitido = {}
            if 'id' in allowed_value:
                valor_permitido['id'] = allowed_value.get('id')
            if 'value' in allowed_value:
                valor_permitido['value'] = allowed_value.get('value')
            if 'key' in allowed_value:
                valor_permitido['key'] = allowed_value.get('key')
            if 'name' in allowed_value:
                valor_permitido['name'] = allowed_value.get('name')
            valores_permitidos.append(valor_permitido)
        item['allowedValues'] = valores_permitidos
        if field is not None and field == campo:
            campos.append(item)
    return json.dumps(campos, indent=2, ensure_ascii=True)

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

def get_instructions_to_create_tarefa() -> str:
    """Provide instructions on how to create a Jira task with custom fields.
    
    Returns:
        A detailed instruction string
    """
    instructions = """To create a Jira task with custom fields, follow these steps:
1. Identify the project key where you want to create the issue (e.g., 'ARQPERF').
2. Determine the issue type (e.g., 'Tarefa', 'SubTarefa').
3. Gather the necessary information: 
    - Title (summary)
    - Description (rich text supported)
    - Assignee email
    - Parent issue key (always required! If is a "Tarefa", must be a Epic. If is a "SubTarefa", must be a "Tarefa". If is not clear, ask to user)
    - Custom fields that *MUST* be filled:
        For task type "Tarefa":
        - customfield_10310 (Estrutura): Must be a value from the allowed options.
        - customfield_10311 (Tipo de Demanda (ARQPERF)): Must be a value from the allowed options.
        - customfield_10058 (Account): Must be a value from the allowed options. 
        - customfield_10312 (Processo): Must be a value from the allowed options. 
        - customfield_10136 (CIP Team): Must be a value from the allowed options. 
        - customfield_10015 (Start Date): Must be a date in YYYY-MM-DD format. Use today if the user do not provide.
        - customfield_10339 (Origem da Demanda): Always ask the user to provide a value from the allowed options.
        - customfield_10307 (Alinhamento) : Try to use the same value from the parent issue. If not possible, ask the user to provide a value from the allowed options.
        - customfield_10308 (Quarter): Is the quarter of the year. Use the current quarter and pick from the allowed values
        - customfield_10309 (Sprint Prevista) : Must be a value from the allowed options. If not possible, ask the user to provide a value from the allowed options.
        
*Remember*: If a custom field has a list of Allowed Values, try to figure out based on current context. If cannot be done, ask the user providing the available options to choose from.
*Always* provide the custom fields values as objects when the type is not a scalar (e.g., single select, multi select, user picker) in the format '{"id": "id of the choice"}' or {"key": "if a key is available for the choice"}

Before creating the issue, print the preview of the issue with all fields filled and ask the user to confirm before proceeding.

Complete example of the request:
{
  "project": "ARQPERF",
  "title": "Análise do problema da RRC0010 MQ em HEXT",
  "issue_type": "Task",
  "description": "Análise do problema da RRC0010 MQ em HEXT. Foi verificado a necessidade detabela faltante em HEXT para processar as requisições na AWS. Foi verificado que não foi criada uma tabela necessaria para o projeto das consultas na AWS em HEXT.\nTambém foi ajustada a configuração da fila que a API de consultas escuta no MQ. Foi feito um deploy da configuração apenas.",
  "parent": "ARQPERF-2463",
  "assignee_email": "luiz.sosinho@nuclea.com.br",
  "custom_fields": {
    "customfield_10310": {
      "id": "11526"
    },
    "customfield_10311": {
      "id": "11538"
    },
    "customfield_10058": 137,
    "customfield_10312": {
      "id": "11542"
    },
    "customfield_10136": {
      "id": "10020"
    },
    "customfield_10015": "2025-09-08",
    "customfield_10339": {
      "id": "11605"
    },
    "customfield_10307": {
      "value": "Alinhada na BRP"
    },
    "customfield_10308": {
      "id": "11480"
    },
    "customfield_10309": {
      "value": "20"
    }
  }
}


"""
    return instructions

def get_instructions_to_create_subtarefa() -> str:
    """Provide instructions on how to create a Jira subtask with custom fields.
    
    Returns:
        A detailed instruction string
    """
    instructions = """Not implemented yet. Tell the user that this feature is not available now."""
    return instructions


@with_jira_client
def get_child_issues_by_parent_impl(parent_key: str) -> Dict[str, Any]:
    """Get all issues that have the specified issue as their parent.
    
    Args:
        parent_key: The key of the parent issue (e.g., 'PROJ-123')
    
    Returns:
        A dictionary containing:
        - parent_info: Basic information about the parent issue
        - children: List of child issues with their details
        - total_children: Count of child issues
    """
    try:
        # First verify if parent exists
        parent = jira_client.issue(parent_key)
        
        # Search for all issues that have this parent
        jql = f'parent = {parent_key} ORDER BY created DESC'
        children = jira_client.search_issues(jql, maxResults=1000)
        
        child_issues = []
        for child in children:
            child_issues.append({
                'key': child.key,
                'title': child.fields.summary,
                'status': child.fields.status.name,
                'issue_type': child.fields.issuetype.name,
                'assignee': getattr(child.fields.assignee, 'displayName', 'Unassigned'),
                'priority': getattr(child.fields.priority, 'name', 'No Priority'),
                'created': str(child.fields.created),
                'updated': str(child.fields.updated)
            })
        
        return {
            'parent_info': {
                'key': parent.key,
                'title': parent.fields.summary,
                'type': parent.fields.issuetype.name,
                'status': parent.fields.status.name
            },
            'children': child_issues,
            'total_children': len(child_issues)
        }
        
    except Exception as e:
        return {
            'error': f"Failed to get child issues: {str(e)}",
            'parent_key': parent_key,
            'children': [],
            'total_children': 0
        }

if __name__ == "__main__":
    campos = get_issue_type_custom_fields_by_project_impl("ARQPERF", "Tarefa", 'customfield_10311')
    print(campos) 
    #campos = get_issue_types_impl()
    #print(campos)