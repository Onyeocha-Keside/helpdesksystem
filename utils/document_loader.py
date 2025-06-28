import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from models.knowledge import (
    Category, 
    InstallationGuide, 
    TroubleshootingStep, 
    KnowledgeDocument,
    CommonIssue
)


class KnowledgeBase:
    """Centralized knowledge base containing all loaded documents."""
    
    def __init__(self):
        self.categories: Dict[str, Category] = {}
        self.installation_guides: Dict[str, InstallationGuide] = {}
        self.troubleshooting_steps: Dict[str, TroubleshootingStep] = {}
        self.documents: List[KnowledgeDocument] = []
        self.policies: str = ""
        self.general_knowledge: str = ""
    
    def add_category(self, name: str, category: Category):
        """Add a category to the knowledge base."""
        self.categories[name] = category
    
    def add_installation_guide(self, software: str, guide: InstallationGuide):
        """Add an installation guide."""
        self.installation_guides[software] = guide
    
    def add_troubleshooting_step(self, issue_type: str, step: TroubleshootingStep):
        """Add troubleshooting steps."""
        self.troubleshooting_steps[issue_type] = step
    
    def add_document(self, document: KnowledgeDocument):
        """Add a knowledge document."""
        self.documents.append(document)
    
    def get_all_text_content(self) -> List[str]:
        """Get all text content for embedding generation."""
        content = []
        
        # Add category descriptions
        for cat_name, category in self.categories.items():
            content.append(f"Category: {cat_name} - {category.description}")
        
        # Add installation guide content
        for software, guide in self.installation_guides.items():
            guide_text = f"Installing {software}: {guide.title}\n"
            guide_text += "Steps: " + "; ".join(guide.steps)
            if guide.common_issues:
                issues = [f"{issue.issue}: {issue.solution}" for issue in guide.common_issues]
                guide_text += "\nCommon issues: " + "; ".join(issues)
            content.append(guide_text)
        
        # Add troubleshooting steps
        for issue_type, steps in self.troubleshooting_steps.items():
            step_text = f"Troubleshooting {issue_type} ({steps.category}): "
            step_text += "; ".join(steps.steps)
            content.append(step_text)
        
        # Add policy content
        if self.policies:
            content.append(self.policies)
        
        # Add general knowledge
        if self.general_knowledge:
            content.append(self.general_knowledge)
        
        # Add document content
        for doc in self.documents:
            content.append(doc.content)
        
        return content


class DocumentLoader:
    """Loads and processes knowledge base documents."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.knowledge_base = KnowledgeBase()
    
    def load_all(self) -> KnowledgeBase:
        """Load all knowledge base files."""
        print(f"Loading knowledge base from {self.data_dir}")
        
        # Load categories
        self._load_categories()
        
        # Load installation guides
        self._load_installation_guides()
        
        # Load troubleshooting database
        self._load_troubleshooting_database()
        
        # Load policy documents
        self._load_policies()
        
        # Load general knowledge base
        self._load_knowledge_base()
        
        print(f"Loaded {len(self.knowledge_base.categories)} categories")
        print(f"Loaded {len(self.knowledge_base.installation_guides)} installation guides")
        print(f"Loaded {len(self.knowledge_base.troubleshooting_steps)} troubleshooting procedures")
        
        return self.knowledge_base
    
    def _load_categories(self):
        """Load categories.json"""
        file_path = self.data_dir / "categories.json"
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for cat_name, cat_data in data.get("categories", {}).items():
            category = Category(
                name=cat_name,
                description=cat_data.get("description", ""),
                typical_resolution_time=cat_data.get("typical_resolution_time", ""),
                escalation_triggers=cat_data.get("escalation_triggers", [])
            )
            self.knowledge_base.add_category(cat_name, category)
    
    def _load_installation_guides(self):
        """Load installation_guides.json"""
        file_path = self.data_dir / "installation_guides.json"
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for software, guide_data in data.get("software_guides", {}).items():
            # Parse common issues
            common_issues = []
            for issue_data in guide_data.get("common_issues", []):
                common_issues.append(CommonIssue(
                    issue=issue_data.get("issue", ""),
                    solution=issue_data.get("solution", "")
                ))
            
            guide = InstallationGuide(
                software=software,
                title=guide_data.get("title", ""),
                steps=guide_data.get("steps", []),
                common_issues=common_issues,
                support_contact=guide_data.get("support_contact", "")
            )
            self.knowledge_base.add_installation_guide(software, guide)
    
    def _load_troubleshooting_database(self):
        """Load troubleshooting_database.json"""
        file_path = self.data_dir / "troubleshooting_database.json"
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for issue_type, step_data in data.get("troubleshooting_steps", {}).items():
            steps = TroubleshootingStep(
                issue_type=issue_type,
                category=step_data.get("category", ""),
                steps=step_data.get("steps", []),
                escalation_trigger=step_data.get("escalation_trigger", ""),
                escalation_contact=step_data.get("escalation_contact", "")
            )
            self.knowledge_base.add_troubleshooting_step(issue_type, steps)
    
    def _load_policies(self):
        """Load company_it_policies.md"""
        file_path = self.data_dir / "company_it_policies.md"
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.knowledge_base.policies = content
        
        # Also add as a document
        doc = KnowledgeDocument(
            source="company_it_policies.md",
            content=content,
            metadata={"type": "policy", "category": "general"}
        )
        self.knowledge_base.add_document(doc)
    
    def _load_knowledge_base(self):
        """Load knowledge_base.md"""
        file_path = self.data_dir / "knowledge_base.md"
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.knowledge_base.general_knowledge = content
        
        # Also add as a document
        doc = KnowledgeDocument(
            source="knowledge_base.md",
            content=content,
            metadata={"type": "knowledge", "category": "general"}
        )
        self.knowledge_base.add_document(doc)
    
    def get_category_names(self) -> List[str]:
        """Get list of all category names."""
        return list(self.knowledge_base.categories.keys())
    
    def get_category_description(self, category_name: str) -> Optional[str]:
        """Get description for a specific category."""
        category = self.knowledge_base.categories.get(category_name)
        return category.description if category else None
    
    def should_escalate(self, category: str, user_message: str = "") -> bool:
        """Check if a request should be escalated based on category rules."""
        category_obj = self.knowledge_base.categories.get(category)
        if not category_obj:
            return False
        
        # Check for automatic escalation categories
        auto_escalate = ["security_incident", "hardware_failure"]
        if category in auto_escalate:
            return True
        
        # Check escalation triggers
        triggers = category_obj.escalation_triggers
        user_message_lower = user_message.lower()
        
        for trigger in triggers:
            if trigger.lower() in user_message_lower:
                return True
        
        return False