import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from models.response import KnowledgeItem
from models.knowledge import KnowledgeDocument
from utils import KnowledgeBase


class KnowledgeRetriever:
    """Retrieves relevant knowledge using semantic search with embeddings (No FAISS dependency)."""
    
    def __init__(self, knowledge_base: KnowledgeBase, embedding_model: str = "all-MiniLM-L6-v2"):
        self.knowledge_base = knowledge_base
        self.embedding_model_name = embedding_model
        self.encoder = None
        self.knowledge_chunks = []  # Store text chunks with metadata
        self.embeddings = None
        
    async def initialize(self):
        """Initialize the embedding model and build the search index."""
        print(f"🔧 Loading embedding model: {self.embedding_model_name}")
        self.encoder = SentenceTransformer(self.embedding_model_name)
        
        print("📝 Preparing knowledge chunks...")
        self._prepare_knowledge_chunks()
        
        print("🔮 Generating embeddings...")
        self._generate_embeddings()
        
        print(f"✅ Knowledge retriever initialized with {len(self.knowledge_chunks)} chunks")
    
    def _prepare_knowledge_chunks(self):
        """Break down knowledge base into searchable chunks."""
        self.knowledge_chunks = []
        
        # Process categories
        for cat_name, category in self.knowledge_base.categories.items():
            chunk = {
                "content": f"Category: {cat_name} - {category.description}. "
                          f"Resolution time: {category.typical_resolution_time}. "
                          f"Escalation triggers: {', '.join(category.escalation_triggers)}",
                "source": f"categories.json:{cat_name}",
                "type": "category",
                "category": cat_name,
                "metadata": {
                    "resolution_time": category.typical_resolution_time,
                    "escalation_triggers": category.escalation_triggers
                }
            }
            self.knowledge_chunks.append(chunk)
        
        # Process installation guides
        for software, guide in self.knowledge_base.installation_guides.items():
            # Main guide chunk
            steps_text = ". ".join(guide.steps)
            chunk = {
                "content": f"Installing {software}: {guide.title}. Steps: {steps_text}",
                "source": f"installation_guides.json:{software}",
                "type": "installation_guide",
                "category": "software_installation",
                "metadata": {
                    "software": software,
                    "support_contact": guide.support_contact
                }
            }
            self.knowledge_chunks.append(chunk)
            
            # Common issues chunks
            for issue in guide.common_issues:
                issue_chunk = {
                    "content": f"{software} issue: {issue.issue}. Solution: {issue.solution}",
                    "source": f"installation_guides.json:{software}:issues",
                    "type": "common_issue",
                    "category": "software_installation",
                    "metadata": {
                        "software": software,
                        "issue_type": "installation",
                        "support_contact": guide.support_contact
                    }
                }
                self.knowledge_chunks.append(issue_chunk)
        
        # Process troubleshooting steps
        for issue_type, steps in self.knowledge_base.troubleshooting_steps.items():
            steps_text = ". ".join(steps.steps)
            chunk = {
                "content": f"Troubleshooting {issue_type} ({steps.category}): {steps_text}. "
                          f"Escalate when: {steps.escalation_trigger}",
                "source": f"troubleshooting_database.json:{issue_type}",
                "type": "troubleshooting",
                "category": self._map_troubleshooting_to_category(issue_type),
                "metadata": {
                    "issue_type": issue_type,
                    "escalation_trigger": steps.escalation_trigger,
                    "escalation_contact": steps.escalation_contact
                }
            }
            self.knowledge_chunks.append(chunk)
        
        # Process policy documents (split into sections)
        if self.knowledge_base.policies:
            policy_sections = self._split_markdown_sections(
                self.knowledge_base.policies, 
                "company_it_policies.md"
            )
            self.knowledge_chunks.extend(policy_sections)
        
        # Process general knowledge base (split into sections)
        if self.knowledge_base.general_knowledge:
            kb_sections = self._split_markdown_sections(
                self.knowledge_base.general_knowledge,
                "knowledge_base.md"
            )
            self.knowledge_chunks.extend(kb_sections)
    
    def _split_markdown_sections(self, content: str, source: str) -> List[Dict[str, Any]]:
        """Split markdown content into logical sections."""
        sections = []
        lines = content.split('\n')
        current_section = []
        current_header = ""
        
        for line in lines:
            if line.strip().startswith('#'):
                # Save previous section
                if current_section and current_header:
                    section_content = '\n'.join(current_section).strip()
                    if section_content:
                        category = self._infer_category_from_header(current_header)
                        sections.append({
                            "content": f"{current_header}: {section_content}",
                            "source": f"{source}:{current_header.replace('#', '').strip()}",
                            "type": "policy" if "policies" in source else "knowledge",
                            "category": category,
                            "metadata": {"section": current_header.strip()}
                        })
                
                # Start new section
                current_header = line.strip()
                current_section = []
            else:
                if line.strip():  # Skip empty lines
                    current_section.append(line)
        
        # Add final section
        if current_section and current_header:
            section_content = '\n'.join(current_section).strip()
            if section_content:
                category = self._infer_category_from_header(current_header)
                sections.append({
                    "content": f"{current_header}: {section_content}",
                    "source": f"{source}:{current_header.replace('#', '').strip()}",
                    "type": "policy" if "policies" in source else "knowledge",
                    "category": category,
                    "metadata": {"section": current_header.strip()}
                })
        
        return sections
    
    def _map_troubleshooting_to_category(self, issue_type: str) -> str:
        """Map troubleshooting issue types to help desk categories."""
        mapping = {
            "password_reset": "password_reset",
            "slow_computer": "hardware_failure",
            "wifi_connection": "network_connectivity",
            "email_not_syncing": "email_configuration",
            "software_installation_failed": "software_installation"
        }
        return mapping.get(issue_type, "policy_question")
    
    def _infer_category_from_header(self, header: str) -> str:
        """Infer category from section header."""
        header_lower = header.lower()
        
        if any(word in header_lower for word in ["password", "login", "authentication"]):
            return "password_reset"
        elif any(word in header_lower for word in ["software", "installation", "install"]):
            return "software_installation"
        elif any(word in header_lower for word in ["hardware", "device", "equipment"]):
            return "hardware_failure"
        elif any(word in header_lower for word in ["network", "connectivity", "wifi", "vpn"]):
            return "network_connectivity"
        elif any(word in header_lower for word in ["email", "mail", "outlook"]):
            return "email_configuration"
        elif any(word in header_lower for word in ["security", "incident", "threat"]):
            return "security_incident"
        else:
            return "policy_question"
    
    def _generate_embeddings(self):
        """Generate embeddings for all knowledge chunks."""
        if not self.knowledge_chunks:
            print("⚠️  No knowledge chunks to embed")
            return
        
        # Extract text content
        texts = [chunk["content"] for chunk in self.knowledge_chunks]
        
        # Generate embeddings using sentence transformers
        print(f"🔮 Generating embeddings for {len(texts)} chunks...")
        self.embeddings = self.encoder.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        
        print(f"📊 Generated {self.embeddings.shape[0]} embeddings of dimension {self.embeddings.shape[1]}")
    
    async def retrieve_knowledge(
        self, 
        query: str, 
        category: str = None, 
        top_k: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[KnowledgeItem]:
        """
        Retrieve relevant knowledge items for a query using cosine similarity.
        
        Args:
            query: User's question or request
            category: Predicted category to filter results
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of relevant KnowledgeItem objects
        """
        if self.embeddings is None or not self.encoder:
            print("⚠️  Knowledge retriever not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode(
                [query], 
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Calculate cosine similarity with all knowledge chunks
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Get indices sorted by similarity (descending)
            sorted_indices = np.argsort(similarities)[::-1]
            
            # Filter and rank results
            results = []
            seen_sources = set()
            
            for idx in sorted_indices:
                similarity_score = similarities[idx]
                
                if similarity_score < similarity_threshold:
                    continue
                
                chunk = self.knowledge_chunks[idx]
                source = chunk["source"]
                
                # Avoid duplicate sources
                if source in seen_sources:
                    continue
                seen_sources.add(source)
                
                # Category filtering (prefer same category, but don't exclude others)
                relevance_boost = 0.0
                if category and chunk.get("category") == category:
                    relevance_boost = 0.1
                
                # Create knowledge item
                knowledge_item = KnowledgeItem(
                    content=chunk["content"],
                    source=source,
                    relevance_score=float(similarity_score + relevance_boost)
                )
                
                results.append(knowledge_item)
                
                if len(results) >= top_k:
                    break
            
            # Sort by relevance score (descending)
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            print(f"🔍 Retrieved {len(results)} knowledge items for category '{category}'")
            return results
            
        except Exception as e:
            print(f"❌ Error in knowledge retrieval: {e}")
            return []
    
    def get_category_specific_knowledge(self, category: str) -> List[KnowledgeItem]:
        """Get all knowledge items specific to a category."""
        items = []
        
        for chunk in self.knowledge_chunks:
            if chunk.get("category") == category:
                item = KnowledgeItem(
                    content=chunk["content"],
                    source=chunk["source"],
                    relevance_score=1.0  # Max relevance for exact category match
                )
                items.append(item)
        
        return items
    
    def search_by_keywords(self, keywords: List[str], top_k: int = 5) -> List[KnowledgeItem]:
        """Simple keyword-based search as fallback."""
        results = []
        
        for chunk in self.knowledge_chunks:
            content_lower = chunk["content"].lower()
            score = sum(1 for keyword in keywords if keyword.lower() in content_lower)
            
            if score > 0:
                item = KnowledgeItem(
                    content=chunk["content"],
                    source=chunk["source"],
                    relevance_score=float(score / len(keywords))
                )
                results.append(item)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]