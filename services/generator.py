from typing import List
from openai import AsyncOpenAI

from models.request import HelpDeskRequest
from models.response import ClassificationResult, KnowledgeItem, EscalationInfo


class ResponseGenerator:
    """Generates contextual responses using OpenAI based on classified requests and retrieved knowledge."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate_response(
        self,
        request: HelpDeskRequest,
        classification: ClassificationResult,
        knowledge_items: List[KnowledgeItem],
        escalation_info: EscalationInfo
    ) -> str:
        """
        Generate a contextual response for the help desk request.
        
        Args:
            request: The original user request
            classification: Classification result with category and confidence
            knowledge_items: Relevant knowledge retrieved from the knowledge base
            escalation_info: Escalation decision and details
            
        Returns:
            Generated response text
        """
        
        # Create the response generation prompt
        prompt = self._create_response_prompt(
            request, 
            classification, 
            knowledge_items, 
            escalation_info
        )
        
        try:
            # Generate response using OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Balanced creativity and consistency
                max_tokens=800    # Reasonable response length
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating response: {e}")
            # Fallback response
            return self._generate_fallback_response(request, classification, escalation_info)
    
    def _get_system_prompt(self) -> str:
        """System prompt defining the AI assistant's role and behavior."""
        return """You are an expert IT Help Desk assistant for TechCorp Inc. Your role is to provide helpful, accurate, and professional responses to employee IT requests.

GUIDELINES:
- Be friendly, professional, and empathetic
- Provide clear, step-by-step instructions when applicable
- Reference company policies and procedures when relevant
- Always include next steps or follow-up actions
- If escalation is required, explain why and provide contact information
- Use the retrieved knowledge to give accurate, company-specific guidance
- Keep responses concise but comprehensive
- Show understanding of the user's urgency and business impact

RESPONSE STRUCTURE:
1. Acknowledge the issue with empathy
2. Provide the solution or next steps
3. Include relevant company-specific information
4. Mention escalation if required
5. Offer additional help or resources

Remember: You represent TechCorp's IT support team, so maintain a professional and helpful tone."""
    
    def _create_response_prompt(
        self,
        request: HelpDeskRequest,
        classification: ClassificationResult,
        knowledge_items: List[KnowledgeItem],
        escalation_info: EscalationInfo
    ) -> str:
        """Create a detailed prompt for response generation."""
        
        prompt = f"""
USER REQUEST: "{request.message}"

CLASSIFICATION:
- Category: {classification.category}
- Confidence: {classification.confidence:.2f}
- Reasoning: {classification.reasoning}

RELEVANT KNOWLEDGE:
"""
        
        # Add retrieved knowledge items
        if knowledge_items:
            for i, item in enumerate(knowledge_items, 1):
                prompt += f"\n{i}. Source: {item.source} (Relevance: {item.relevance_score:.2f})\n"
                prompt += f"   Content: {item.content}\n"
        else:
            prompt += "\nNo specific knowledge retrieved - provide general guidance based on category.\n"
        
        # Add escalation information
        prompt += f"\nESCALATION INFO:\n"
        prompt += f"- Required: {escalation_info.required}\n"
        if escalation_info.required:
            prompt += f"- Reason: {escalation_info.reason}\n"
            prompt += f"- Contact: {escalation_info.contact}\n"
            prompt += f"- Urgency: {escalation_info.urgency}\n"
        
        # Add request context
        if request.priority and request.priority != "normal":
            prompt += f"\nREQUEST PRIORITY: {request.priority.upper()}\n"
        
        if request.user_id:
            prompt += f"USER: {request.user_id}\n"
        
        # Specific instructions based on category
        category_instructions = self._get_category_specific_instructions(classification.category)
        prompt += f"\nCATEGORY-SPECIFIC GUIDANCE:\n{category_instructions}\n"
        
        prompt += """
GENERATE A HELPFUL RESPONSE:
Create a professional, empathetic response that addresses the user's issue. Include:
1. Acknowledgment of their problem
2. Clear solution steps or guidance
3. Company-specific information from the knowledge base
4. Escalation information if required
5. Next steps or follow-up actions
"""
        
        return prompt
    
    def _get_category_specific_instructions(self, category: str) -> str:
        """Get specific instructions for each category."""
        
        instructions = {
            "password_reset": """
- Guide them to the self-service password reset portal
- Mention password policy requirements
- Explain account lockout procedures
- Provide IT contact for persistent issues
""",
            "software_installation": """
- Check if software is approved for installation
- Provide installation steps with administrator privileges
- Include troubleshooting for common installation issues
- Mention manager approval requirements for new software
""",
            "hardware_failure": """
- Acknowledge urgency of hardware issues
- Advise on data backup if possible
- Explain hardware replacement timeline
- Mention temporary equipment availability
- Always escalate to hardware support team
""",
            "network_connectivity": """
- Provide basic network troubleshooting steps
- Check for widespread network issues
- Include VPN troubleshooting if relevant
- Escalate if multiple users affected
""",
            "email_configuration": """
- Provide email server settings (IMAP/SMTP)
- Check for mailbox storage issues
- Include synchronization troubleshooting
- Mention email admin for server-side issues
""",
            "security_incident": """
- Take security concerns seriously
- Advise immediate reporting to security team
- Instruct not to attempt fixes themselves
- Emphasize evidence preservation
- Always escalate to security team
""",
            "policy_question": """
- Reference relevant company IT policies
- Provide clear policy explanations
- Include approval processes if applicable
- Direct to appropriate contacts for exceptions
"""
        }
        
        return instructions.get(category, "Provide general IT support guidance appropriate for the request.")
    
    def _generate_fallback_response(
        self,
        request: HelpDeskRequest,
        classification: ClassificationResult,
        escalation_info: EscalationInfo
    ) -> str:
        """Generate a fallback response when OpenAI fails."""
        
        response = f"Hello! I understand you're experiencing a {classification.category.replace('_', ' ')} issue. "
        
        # Category-specific fallback responses
        fallback_responses = {
            "password_reset": "For password issues, please visit https://password.techcorp.com to reset your password using your company email address. If you continue to have issues, please contact IT support at it-support@techcorp.com.",
            
            "software_installation": "For software installation help, please ensure you're running the installer as an administrator. If you need new software installed, please check with your manager for approval and contact IT support for assistance.",
            
            "hardware_failure": "Hardware issues require immediate attention. Please contact our hardware support team immediately and avoid using the affected device to prevent data loss. We'll arrange replacement equipment as needed.",
            
            "network_connectivity": "For network connectivity issues, please try restarting your network adapter and check with colleagues if they're experiencing similar issues. If the problem persists, please contact network support.",
            
            "email_configuration": "For email configuration issues, please check your internet connection and verify your email settings. If you continue to have problems, please contact our email support team.",
            
            "security_incident": "Security incidents require immediate attention. Please do not attempt to fix the issue yourself. Contact our security team immediately at security@techcorp.com and preserve any evidence.",
            
            "policy_question": "For IT policy questions, please refer to our company IT policies or contact IT support for clarification. We're here to help ensure you're following the correct procedures."
        }
        
        category_response = fallback_responses.get(
            classification.category, 
            "I'll help you with your IT request. Please contact our IT support team for immediate assistance."
        )
        
        response += category_response
        
        # Add escalation information
        if escalation_info.required:
            response += f"\n\nThis issue requires escalation to our specialized team. "
            if escalation_info.contact:
                response += f"Please contact {escalation_info.contact} for immediate assistance."
            if escalation_info.reason:
                response += f" Reason: {escalation_info.reason}"
        
        response += "\n\nIs there anything else I can help you with today?"
        
        return response