from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ClassificationResult(BaseModel):
    """Result of request classification."""
    
    category: str = Field(..., description="Classified category")
    confidence: float = Field(..., description="Classification confidence (0-1)")
    reasoning: Optional[str] = Field(None, description="Explanation of classification")
    
    class Config:
        schema_extra = {
            "example": {
                "category": "password_reset",
                "confidence": 0.95,
                "reasoning": "User explicitly mentions forgotten password and login issues"
            }
        }


class KnowledgeItem(BaseModel):
    """Knowledge base item retrieved for response."""
    
    content: str = Field(..., description="Relevant knowledge content")
    source: str = Field(..., description="Source document/section")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    
    class Config:
        schema_extra = {
            "example": {
                "content": "Go to https://password.techcorp.com and enter your company email",
                "source": "troubleshooting_database.json:password_reset",
                "relevance_score": 0.89
            }
        }


class EscalationInfo(BaseModel):
    """Information about escalation decision."""
    
    required: bool = Field(..., description="Whether escalation is required")
    reason: Optional[str] = Field(None, description="Reason for escalation")
    contact: Optional[str] = Field(None, description="Escalation contact")
    urgency: Optional[str] = Field(None, description="Escalation urgency level")
    
    class Config:
        schema_extra = {
            "example": {
                "required": True,
                "reason": "Hardware failure requiring immediate attention",
                "contact": "hardware-support@techcorp.com",
                "urgency": "high"
            }
        }


class HelpDeskResponse(BaseModel):
    """Complete help desk response."""
    
    request_id: str = Field(..., description="Original request ID")
    category: str = Field(..., description="Classified category")
    response: str = Field(..., description="Generated response text")
    
    # Classification details
    classification: ClassificationResult = Field(..., description="Classification details")
    
    # Knowledge retrieval
    knowledge_items: List[KnowledgeItem] = Field(default=[], description="Retrieved knowledge items")
    
    # Escalation information
    escalation: EscalationInfo = Field(..., description="Escalation details")
    
    # Processing metadata
    processing_time: float = Field(..., description="Total processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_001",
                "category": "password_reset",
                "response": "I can help you reset your password. Please go to https://password.techcorp.com...",
                "classification": {
                    "category": "password_reset",
                    "confidence": 0.95,
                    "reasoning": "User explicitly mentions forgotten password"
                },
                "knowledge_items": [
                    {
                        "content": "Go to password reset portal",
                        "source": "troubleshooting_database.json",
                        "relevance_score": 0.89
                    }
                ],
                "escalation": {
                    "required": False,
                    "reason": None,
                    "contact": None,
                    "urgency": None
                },
                "processing_time": 1.23,
                "timestamp": "2025-06-26T10:30:15Z"
            }
        }