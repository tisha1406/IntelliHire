from enum import Enum
from typing import List, Dict

class Permission(str, Enum):
    # Campaign permissions
    VIEW_CAMPAIGNS = "VIEW_CAMPAIGNS"
    CREATE_CAMPAIGNS = "CREATE_CAMPAIGNS"
    EDIT_CAMPAIGNS = "EDIT_CAMPAIGNS"
    DELETE_CAMPAIGNS = "DELETE_CAMPAIGNS"
    
    # Candidate permissions
    VIEW_CANDIDATES = "VIEW_CANDIDATES"
    CREATE_CANDIDATES = "CREATE_CANDIDATES"
    EDIT_CANDIDATES = "EDIT_CANDIDATES"
    DELETE_CANDIDATES = "DELETE_CANDIDATES"
    ASSIGN_CANDIDATES = "ASSIGN_CANDIDATES"
    
    # Team permissions
    VIEW_TEAM = "VIEW_TEAM"
    MANAGE_TEAM = "MANAGE_TEAM"
    
    # Analytics permissions
    VIEW_REPORTS = "VIEW_REPORTS"

# Define standard roles
class SubRole(str, Enum):
    OWNER = "owner"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    VIEWER = "viewer"

# Map sub-roles to permissions
ROLE_PERMISSIONS: Dict[SubRole, List[Permission]] = {
    SubRole.OWNER: [
        Permission.VIEW_CAMPAIGNS, Permission.CREATE_CAMPAIGNS, Permission.EDIT_CAMPAIGNS, Permission.DELETE_CAMPAIGNS,
        Permission.VIEW_CANDIDATES, Permission.CREATE_CANDIDATES, Permission.EDIT_CANDIDATES, Permission.DELETE_CANDIDATES, Permission.ASSIGN_CANDIDATES,
        Permission.VIEW_TEAM, Permission.MANAGE_TEAM,
        Permission.VIEW_REPORTS
    ],
    SubRole.HR_MANAGER: [
        Permission.VIEW_CAMPAIGNS, Permission.CREATE_CAMPAIGNS, Permission.EDIT_CAMPAIGNS,
        Permission.VIEW_CANDIDATES, Permission.CREATE_CANDIDATES, Permission.EDIT_CANDIDATES, Permission.ASSIGN_CANDIDATES,
        Permission.VIEW_TEAM, Permission.MANAGE_TEAM,
        Permission.VIEW_REPORTS
    ],
    SubRole.RECRUITER: [
        Permission.VIEW_CAMPAIGNS,
        Permission.VIEW_CANDIDATES, Permission.CREATE_CANDIDATES, Permission.EDIT_CANDIDATES,
        Permission.VIEW_TEAM,
        Permission.VIEW_REPORTS
    ],
    SubRole.VIEWER: [
        Permission.VIEW_CAMPAIGNS,
        Permission.VIEW_CANDIDATES,
        Permission.VIEW_TEAM,
        Permission.VIEW_REPORTS
    ]
}

def get_permissions_for_role(role: str) -> List[Permission]:
    """Returns a list of permissions for a given sub-role. Defaults to VIEWER if unknown."""
    try:
        sub_role = SubRole(role.lower())
        return ROLE_PERMISSIONS[sub_role]
    except ValueError:
        # If the role is just standard "company" or unknown, give them OWNER for backward compatibility
        if role.lower() == "company":
            return ROLE_PERMISSIONS[SubRole.OWNER]
        return ROLE_PERMISSIONS[SubRole.VIEWER]
