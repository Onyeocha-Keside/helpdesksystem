from typing import Dict, List
from models.response import EscalationInfo
from utils import KnowledgeBase


class EscalationManager:
    """Manages escalation logic based on categories, triggers, and confidence levels."""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base
        
        # Define escalation contacts for each category
        self.escalation_contacts = {
            "password_reset": "security@techcorp.com",
            "software_installation": "software-support@techcorp.com",
            "hardware_failure": "hardware-support@techcorp.com",
            "network_connectivity": "network-support@techcorp.com",
            "email_configuration": "email-support@techcorp.com",
            "security_incident": "security@techcorp.com",
            "policy_question": "it-support@techcorp.com"
        }
        
        # Categories that always require escalation
        self.auto_escalate_categories = {
            "security_incident": "All security incidents require immediate security team attention",
            "hardware_failure": "All hardware failures require specialized technical support"
        }
        
        # Keywords that trigger escalation regardless of category
        self.escalation_keywords = {
            "urgent": "high",
            "emergency": "critical",
            "critical": "critical", 
            "down": "high",
            "broken": "high",
            "not working": "high",
            "can't work": "high",
            "production": "critical",
            "server": "high",
            "multiple users": "high",
            "everyone": "high",
            "department": "high",
            "virus": "critical",
            "hacked": "critical",
            "malware": "critical",
            "suspicious": "high",
            "data loss": "critical",
            "corrupted": "high"
        }
    
    def check_escalation(
        self, 
        category: str, 
        user_message: str, 
        confidence: float = 1.0
    ) -> EscalationInfo:
        """
        Determine if a request requires escalation.
        
        Args:
            category: The classified category
            user_message: Original user message
            confidence: Classification confidence level
            
        Returns:
            EscalationInfo with escalation decision and details
        """
        
        # Check for automatic escalation categories
        if category in self.auto_escalate_categories:
            return EscalationInfo(
                required=True,
                reason=self.auto_escalate_categories[category],
                contact=self.escalation_contacts.get(category, "it-support@techcorp.com"),
                urgency="high" if category == "security_incident" else "medium"
            )
        
        # Check category-specific escalation triggers
        escalation_reason = self._check_category_triggers(category, user_message)
        if escalation_reason:
            urgency = self._determine_urgency(user_message)
            return EscalationInfo(
                required=True,
                reason=escalation_reason,
                contact=self.escalation_contacts.get(category, "it-support@techcorp.com"),
                urgency=urgency
            )
        
        # Check for keyword-based escalation
        keyword_urgency = self._check_keyword_escalation(user_message)
        if keyword_urgency:
            return EscalationInfo(
                required=True,
                reason=f"Request contains keywords indicating {keyword_urgency} priority issue",
                contact=self.escalation_contacts.get(category, "it-support@techcorp.com"),
                urgency=keyword_urgency
            )
        
        # Check low confidence classification
        if confidence < 0.3:
            return EscalationInfo(
                required=True,
                reason=f"Low classification confidence ({confidence:.2f}) - human review recommended",
                contact="it-support@techcorp.com",
                urgency="low"
            )
        
        # No escalation required
        return EscalationInfo(
            required=False,
            reason=None,
            contact=None,
            urgency=None
        )
    
    def _check_category_triggers(self, category: str, user_message: str) -> str:
        """Check for category-specific escalation triggers."""
        
        category_obj = self.knowledge_base.categories.get(category)
        if not category_obj:
            return None
        
        user_message_lower = user_message.lower()
        
        # Check each escalation trigger for this category
        for trigger in category_obj.escalation_triggers:
            trigger_lower = trigger.lower()
            
            # Check for specific trigger phrases
            if any(phrase in user_message_lower for phrase in [
                "multiple failed", "failed multiple", "several attempts",
                "tried many times", "keep failing", "still not working"
            ]) and "reset" in trigger_lower:
                return f"Multiple failed attempts detected: {trigger}"
            
            # Check for security-related triggers
            if any(phrase in user_message_lower for phrase in [
                "security concern", "account compromised", "suspicious activity",
                "unauthorized access", "strange behavior"
            ]) and "security" in trigger_lower:
                return f"Security concern identified: {trigger}"
            
            # Check for approval-related triggers
            if any(phrase in user_message_lower for phrase in [
                "new software", "install software", "need approval",
                "not approved", "custom software"
            ]) and "approval" in trigger_lower:
                return f"Approval required: {trigger}"
            
            # Check for infrastructure issues
            if any(phrase in user_message_lower for phrase in [
                "network down", "wifi down", "internet down", "can't connect",
                "no one can", "everyone having", "whole office"
            ]) and "infrastructure" in trigger_lower:
                return f"Infrastructure issue detected: {trigger}"
        
        return None
    
    def _check_keyword_escalation(self, user_message: str) -> str:
        """Check for escalation based on keywords in the message."""
        
        user_message_lower = user_message.lower()
        highest_urgency = None
        urgency_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        max_level = 0
        
        for keyword, urgency in self.escalation_keywords.items():
            if keyword in user_message_lower:
                level = urgency_levels.get(urgency, 0)
                if level > max_level:
                    max_level = level
                    highest_urgency = urgency
        
        return highest_urgency
    
    def _determine_urgency(self, user_message: str) -> str:
        """Determine urgency level based on message content."""
        
        user_message_lower = user_message.lower()
        
        # Critical urgency indicators
        critical_indicators = [
            "emergency", "critical", "urgent", "asap", "immediately",
            "production down", "server down", "system down",
            "data loss", "corrupted", "virus", "hacked", "malware"
        ]
        
        # High urgency indicators  
        high_indicators = [
            "important meeting", "deadline", "presentation",
            "can't work", "blocking", "stopped working",
            "multiple people", "department", "team affected"
        ]
        
        # Medium urgency indicators
        medium_indicators = [
            "soon", "today", "this morning", "this afternoon",
            "affecting work", "slowing down"
        ]
        
        for indicator in critical_indicators:
            if indicator in user_message_lower:
                return "critical"
        
        for indicator in high_indicators:
            if indicator in user_message_lower:
                return "high"
        
        for indicator in medium_indicators:
            if indicator in user_message_lower:
                return "medium"
        
        return "low"
    
    def get_escalation_contact(self, category: str) -> str:
        """Get the appropriate escalation contact for a category."""
        return self.escalation_contacts.get(category, "it-support@techcorp.com")
    
    def should_auto_escalate(self, category: str) -> bool:
        """Check if a category requires automatic escalation."""
        return category in self.auto_escalate_categories