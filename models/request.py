from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserRequest(BaseModel):
    """Model for incoming user requests."""
    
    message: str = Field(..., description="The user's help request message")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    priority: Optional[str] = Field("normal", description="Request priority (low, normal, high, urgent)")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "I forgot my password and can't log into my computer. How do I reset it?",
                "user_id": "john.doe@techcorp.com",
                "priority": "normal"
            }
        }


class HelpDeskRequest(BaseModel):
    """Internal model for processing help desk requests."""
    
    id: str = Field(..., description="Unique request identifier")
    message: str = Field(..., description="The user's help request message")
    user_id: Optional[str] = Field(None, description="User identifier")
    priority: str = Field("normal", description="Request priority")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    
    # Processing fields
    category: Optional[str] = Field(None, description="Classified category")
    confidence: Optional[float] = Field(None, description="Classification confidence score")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "req_001",
                "message": "I forgot my password and can't log into my computer",
                "user_id": "john.doe@techcorp.com",
                "priority": "normal",
                "timestamp": "2025-06-26T10:30:00Z",
                "category": "password_reset",
                "confidence": 0.95
            }
        }