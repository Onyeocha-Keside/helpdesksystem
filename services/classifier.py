import json
from typing import List, Dict, Any
from openai import AsyncOpenAI

from models.response import ClassificationResult


class RequestClassifier:
    """Classifies help desk requests into predefined categories using OpenAI."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def classify_request(self, user_message: str, categories: List[str]) -> ClassificationResult:
        """
        Classify a user request into one of the predefined categories.
        
        Args:
            user_message: The user's help request message
            categories: List of available category names
            
        Returns:
            ClassificationResult with category, confidence, and reasoning
        """
        
        # Create the classification prompt
        prompt = self._create_classification_prompt(user_message, categories)
        
        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert IT help desk classifier. Analyze user requests and classify them into the most appropriate category with high accuracy."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=500
            )
            
            # Parse the response
            result = self._parse_classification_response(
                response.choices[0].message.content,
                categories,
                user_message
            )
            
            return result
            
        except Exception as e:
            print(f"Error in request classification: {e}")
            # Fallback to default classification
            return ClassificationResult(
                category="policy_question",  # Safe default
                confidence=0.1,
                reasoning=f"Classification failed: {str(e)}"
            )
    
    def _create_classification_prompt(self, user_message: str, categories: List[str]) -> str:
        """Create a detailed prompt for request classification."""
        
        # Category descriptions for better classification
        category_descriptions = {
            "password_reset": "Password-related issues including resets, lockouts, forgotten passwords, and password policy questions",
            "software_installation": "Issues with installing, updating, or configuring software applications",
            "hardware_failure": "Physical hardware problems requiring repair or replacement (laptops, monitors, keyboards, etc.)",
            "network_connectivity": "Network access issues including WiFi, VPN, internet connectivity, and network configuration",
            "email_configuration": "Email setup, synchronization, configuration issues, and mailbox problems",
            "security_incident": "Potential security threats, malware, suspicious activity, or cybersecurity concerns",
            "policy_question": "Questions about company IT policies, procedures, and general IT guidance"
        }
        
        prompt = f"""
Classify the following IT help desk request into one of the predefined categories.

USER REQUEST: "{user_message}"

AVAILABLE CATEGORIES:
"""
        
        for category in categories:
            description = category_descriptions.get(category, "General IT support category")
            prompt += f"- {category}: {description}\n"
        
        prompt += f"""

CLASSIFICATION REQUIREMENTS:
1. Choose the MOST APPROPRIATE category based on the user's primary issue
2. Provide a confidence score between 0.0 and 1.0 (1.0 = completely certain)
3. Explain your reasoning briefly

RESPONSE FORMAT (JSON):
{{
    "category": "selected_category_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this category was chosen"
}}

Key classification guidelines:
- If user mentions "password", "login", "forgot", "locked out" → password_reset
- If user mentions "install", "software", "application", "download" → software_installation  
- If user mentions "broken", "not working", "hardware", "screen", "laptop" → hardware_failure
- If user mentions "WiFi", "internet", "VPN", "network", "connectivity" → network_connectivity
- If user mentions "email", "Outlook", "sync", "mailbox" → email_configuration
- If user mentions "virus", "malware", "security", "suspicious", "hacked" → security_incident
- If user asks about "policy", "procedure", "allowed", "rules" → policy_question

Provide your classification:"""
        
        return prompt
    
    def _parse_classification_response(self, response_text: str, categories: List[str], user_message: str) -> ClassificationResult:
        """Parse the OpenAI response into a ClassificationResult."""
        
        try:
            # Try to parse as JSON
            response_text = response_text.strip()
            
            # Extract JSON if it's wrapped in markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            # Parse JSON
            parsed = json.loads(response_text)
            
            category = parsed.get("category", "").strip()
            confidence = float(parsed.get("confidence", 0.0))
            reasoning = parsed.get("reasoning", "").strip()
            
            # Validate category
            if category not in categories:
                # Try to find closest match
                category_lower = category.lower()
                for valid_cat in categories:
                    if category_lower in valid_cat.lower() or valid_cat.lower() in category_lower:
                        category = valid_cat
                        break
                else:
                    # Default fallback
                    category = "policy_question"
                    confidence = max(0.1, confidence * 0.5)  # Reduce confidence
                    reasoning = f"Original category '{category}' not found. {reasoning}"
            
            # Validate confidence
            confidence = max(0.0, min(1.0, confidence))
            
            return ClassificationResult(
                category=category,
                confidence=confidence,
                reasoning=reasoning or "No reasoning provided"
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Failed to parse classification response: {e}")
            print(f"Response text: {response_text}")
            
            # Fallback classification using keyword matching
            return self._fallback_classification(user_message, categories)
    
    def _fallback_classification(self, message: str, categories: List[str]) -> ClassificationResult:
        """Fallback classification using simple keyword matching."""
        
        message_lower = message.lower()
        
        # Define keyword patterns for each category
        patterns = {
            "password_reset": ["password", "login", "forgot", "reset", "locked", "lockout", "sign in"],
            "software_installation": ["install", "software", "application", "app", "download", "setup"],
            "hardware_failure": ["broken", "not working", "hardware", "screen", "laptop", "monitor", "keyboard"],
            "network_connectivity": ["wifi", "internet", "vpn", "network", "connectivity", "connection"],
            "email_configuration": ["email", "outlook", "sync", "mailbox", "mail"],
            "security_incident": ["virus", "malware", "security", "suspicious", "hacked", "threat"],
            "policy_question": ["policy", "procedure", "allowed", "rules", "guidelines"]
        }
        
        # Score each category
        scores = {}
        for category in categories:
            if category in patterns:
                score = sum(1 for keyword in patterns[category] if keyword in message_lower)
                if score > 0:
                    scores[category] = score
        
        if scores:
            # Get category with highest score
            best_category = max(scores, key=scores.get)
            confidence = min(0.8, scores[best_category] / 3.0)  # Conservative confidence
            reasoning = f"Fallback classification based on keywords: {patterns[best_category]}"
        else:
            # Ultimate fallback
            best_category = "policy_question"
            confidence = 0.1
            reasoning = "No clear indicators found, defaulting to policy question"
        
        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            reasoning=reasoning
        )