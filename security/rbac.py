"""
Role-Based Access Control (RBAC)
Manages user roles and permissions for secure access control.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Permission(Enum):
    """System permissions."""
    # Decision permissions
    VIEW_DECISIONS = "view_decisions"
    MAKE_DECISIONS = "make_decisions"
    OVERRIDE_DECISIONS = "override_decisions"
    
    # HITL permissions
    VIEW_HITL_TASKS = "view_hitl_tasks"
    PROCESS_HITL_TASKS = "process_hitl_tasks"
    MANAGE_HITL_QUEUE = "manage_hitl_queue"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_ANALYTICS = "export_analytics"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    CONFIGURE_SYSTEM = "configure_system"
    VIEW_AUDIT_LOGS = "view_audit_logs"


class Role(Enum):
    """System roles."""
    ADMIN = "admin"
    UNDERWRITER = "underwriter"
    REVIEWER = "reviewer"
    ANALYST = "analyst"
    VIEWER = "viewer"


class RBAC:
    """
    Role-Based Access Control system.
    
    Manages user roles and permissions for secure access control.
    """
    
    def __init__(self):
        """Initialize RBAC system."""
        self.enabled = os.getenv("RBAC_ENABLED", "false").lower() == "true"
        
        # Role permissions mapping
        self.role_permissions = {
            Role.ADMIN: {
                Permission.VIEW_DECISIONS,
                Permission.MAKE_DECISIONS,
                Permission.OVERRIDE_DECISIONS,
                Permission.VIEW_HITL_TASKS,
                Permission.PROCESS_HITL_TASKS,
                Permission.MANAGE_HITL_QUEUE,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_ANALYTICS,
                Permission.MANAGE_USERS,
                Permission.MANAGE_ROLES,
                Permission.CONFIGURE_SYSTEM,
                Permission.VIEW_AUDIT_LOGS
            },
            Role.UNDERWRITER: {
                Permission.VIEW_DECISIONS,
                Permission.MAKE_DECISIONS,
                Permission.VIEW_HITL_TASKS,
                Permission.PROCESS_HITL_TASKS,
                Permission.VIEW_ANALYTICS
            },
            Role.REVIEWER: {
                Permission.VIEW_DECISIONS,
                Permission.VIEW_HITL_TASKS,
                Permission.PROCESS_HITL_TASKS,
                Permission.MANAGE_HITL_QUEUE,
                Permission.VIEW_ANALYTICS
            },
            Role.ANALYST: {
                Permission.VIEW_DECISIONS,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_ANALYTICS
            },
            Role.VIEWER: {
                Permission.VIEW_DECISIONS,
                Permission.VIEW_ANALYTICS
            }
        }
        
        # User roles
        self.user_roles = {}
        
        logger.info(f"RBAC system initialized (enabled={self.enabled})")
    
    def assign_role(self, user_id: str, role: str):
        """
        Assign a role to a user.
        
        Args:
            user_id: User ID
            role: Role name
        """
        if not self.enabled:
            return
        
        try:
            role_enum = Role(role.lower())
            self.user_roles[user_id] = role_enum
            logger.info(f"Assigned role {role} to user {user_id}")
        except ValueError:
            logger.error(f"Invalid role: {role}")
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get permissions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Set of permissions
        """
        if not self.enabled:
            # If disabled, grant all permissions
            return set(Permission)
        
        if user_id not in self.user_roles:
            return set()
        
        role = self.user_roles[user_id]
        return self.role_permissions.get(role, set())
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: User ID
            permission: Permission to check
            
        Returns:
            True if user has permission
        """
        if not self.enabled:
            return True
        
        user_permissions = self.get_user_permissions(user_id)
        
        try:
            permission_enum = Permission(permission.lower())
            return permission_enum in user_permissions
        except ValueError:
            return False
    
    def has_any_permission(self, user_id: str, permissions: List[str]) -> bool:
        """
        Check if a user has any of the specified permissions.
        
        Args:
            user_id: User ID
            permissions: List of permissions to check
            
        Returns:
            True if user has any of the permissions
        """
        if not self.enabled:
            return True
        
        user_permissions = self.get_user_permissions(user_id)
        
        for permission in permissions:
            try:
                permission_enum = Permission(permission.lower())
                if permission_enum in user_permissions:
                    return True
            except ValueError:
                continue
        
        return False
    
    def get_user_role(self, user_id: str) -> Optional[str]:
        """
        Get the role for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Role name or None if not found
        """
        if user_id in self.user_roles:
            return self.user_roles[user_id].value
        return None
    
    def remove_user(self, user_id: str):
        """
        Remove a user (revoke all permissions).
        
        Args:
            user_id: User ID
        """
        if user_id in self.user_roles:
            del self.user_roles[user_id]
            logger.info(f"Removed user {user_id}")
    
    def get_all_users(self) -> Dict[str, str]:
        """
        Get all users and their roles.
        
        Returns:
            Dictionary of user_id -> role
        """
        return {
            user_id: role.value
            for user_id, role in self.user_roles.items()
        }
    
    def get_users_by_role(self, role: str) -> List[str]:
        """
        Get all users with a specific role.
        
        Args:
            role: Role name
            
        Returns:
            List of user IDs
        """
        try:
            role_enum = Role(role.lower())
            return [
                user_id for user_id, user_role in self.user_roles.items()
                if user_role == role_enum
            ]
        except ValueError:
            return []


# Global RBAC instance
_global_rbac: Optional[RBAC] = None


def get_rbac() -> RBAC:
    """
    Get global RBAC instance (singleton pattern).
    
    Returns:
        RBAC instance
    """
    global _global_rbac
    if _global_rbac is None:
        _global_rbac = RBAC()
    return _global_rbac


# Decorator for permission checking
def require_permission(permission: str):
    """
    Decorator to check if user has required permission.
    
    Args:
        permission: Required permission
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            rbac = get_rbac()
            user_id = kwargs.get("user_id", "default_user")
            
            if not rbac.has_permission(user_id, permission):
                logger.warning(f"User {user_id} lacks permission {permission}")
                raise PermissionError(f"User {user_id} lacks permission {permission}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
