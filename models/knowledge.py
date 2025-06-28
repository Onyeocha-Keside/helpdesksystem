from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Category(BaseModel):
    """Help desk category definition."""
    
    name: str = Field(..., description="Category name")
    description: str = Field(..., description="Category description")
    typical_resolution_time: str = Field(..., description="Expected resolution time")
    escalation_triggers: List[str] = Field(default=[], description="Conditions that trigger escalation")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "password_reset",
                "description": "Password-related issues including resets, lockouts, and policy questions",
                "typical_resolution_time": "5-10 minutes",
                "escalation_triggers": ["Multiple failed resets", "Account security concerns"]
            }
        }


class CommonIssue(BaseModel):
    """Common issue and solution pair."""
    
    issue: str = Field(..., description="Description of the issue")
    solution: str = Field(..., description="Solution or workaround")


class InstallationGuide(BaseModel):
    """Software installation guide."""
    
    software: str = Field(..., description="Software name")
    title: str = Field(..., description="Guide title")
    steps: List[str] = Field(..., description="Installation steps")
    common_issues: List[CommonIssue] = Field(default=[], description="Common issues and solutions")
    support_contact: str = Field(..., description="Support contact for this software")
    
    class Config:
        schema_extra = {
            "example": {
                "software": "slack",
                "title": "Installing Slack Desktop App",
                "steps": [
                    "Download Slack from https://slack.com/downloads",
                    "Run the installer with administrator privileges"
                ],
                "common_issues": [
                    {
                        "issue": "Cannot sign in with company email",
                        "solution": "Check with IT - your account may not be provisioned yet"
                    }
                ],
                "support_contact": "it-support@techcorp.com"
            }
        }


class TroubleshootingStep(BaseModel):
    """Troubleshooting procedure."""
    
    issue_type: str = Field(..., description="Type of issue this addresses")
    category: str = Field(..., description="Problem category")
    steps: List[str] = Field(..., description="Troubleshooting steps")
    escalation_trigger: str = Field(..., description="When to escalate")
    escalation_contact: str = Field(..., description="Who to escalate to")
    
    class Config:
        schema_extra = {
            "example": {
                "issue_type": "password_reset",
                "category": "Authentication",
                "steps": [
                    "Go to https://password.techcorp.com",
                    "Enter your company email address"
                ],
                "escalation_trigger": "Multiple failed reset attempts",
                "escalation_contact": "security@techcorp.com"
            }
        }


class KnowledgeDocument(BaseModel):
    """Complete knowledge document structure."""
    
    source: str = Field(..., description="Source file name")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    embeddings: Optional[List[float]] = Field(None, description="Vector embeddings")
    
    class Config:
        schema_extra = {
            "example": {
                "source": "company_it_policies.md",
                "content": "Password Policy - Minimum 12 characters...",
                "metadata": {"section": "Password Policy", "category": "security"},
                "embeddings": [0.1, 0.2, 0.3]  # Simplified example
            }
        }