"""Workflow capability names; no runtime or production authority is granted here."""
from enum import Enum

class Permission(str, Enum):
    MANAGED_INSTALL = "managedInstall"
    MANAGED_UPDATE = "managedUpdate"
    MANAGED_VERIFY = "managedVerify"
    MANAGED_UNINSTALL = "managedUninstall"
    PROJECT_SKILLS = "projectSkills"
    PROJECT_AGENTS = "projectAgents"
    ORCHESTRATION = "orchestration"
    MANAGED_WORKTREE = "managedWorktree"
    RELEASE_SUPPORT_CLAIM = "releaseSupportClaim"
