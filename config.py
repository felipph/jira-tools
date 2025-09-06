# Configuration for field blacklists by issue type
FIELD_BLACKLIST = {
    'Subtarefa': [
        'customfield_10073',
        'customfield_10175',
        'customfield_10274',
        'customfield_10176',
        'customfield_10286',
        'customfield_10000',
        'customfield_10155',
        'customfield_10002',
        'customfield_10019',
        'customfield_11265',
        'customfield_10136',
    ]
}

# Fields that should always be excluded regardless of issue type
GLOBAL_BLACKLIST = [
    'rankBeforeIssue',
    'rankAfterIssue',
    'io.tempo.jira__account',
    'customfield_10014',  # Usually represents the epic link
    'customfield_10020',  # Sprint field
]

def get_blacklisted_fields(issue_type: str) -> list:
    """Get the list of blacklisted fields for a given issue type."""
    type_specific_blacklist = FIELD_BLACKLIST.get(issue_type, [])
    return type_specific_blacklist + GLOBAL_BLACKLIST
