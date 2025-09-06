from typing import Optional
from src.core.jira.jira_integration import get_issue_type_custom_fields_by_project_impl, get

if __name__ == "__main__":
    # Get fields for a specific issue type
    try:
        # Replace with your project key and issue type
        fields_info = get_issue_type_custom_fields_by_project_impl("ARQPERF", "Tarefa")
        print(fields_info)
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
