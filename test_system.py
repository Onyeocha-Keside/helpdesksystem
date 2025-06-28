"""
Quick test script to verify the help desk system works end-to-end.
Run this after setting up your environment and adding your OpenAI API key.
"""

import asyncio
import json
from config import get_settings
from models import UserRequest
from utils import DocumentLoader
from services import RequestClassifier, KnowledgeRetriever, ResponseGenerator, EscalationManager


async def test_help_desk_system():
    """Test the complete help desk system pipeline."""
    
    print("🧪 Testing Intelligent Help Desk System")
    print("=" * 50)
    
    # Load configuration
    settings = get_settings()
    print(f"📋 Using OpenAI model: {settings.openai_model}")
    
    # Initialize components
    print("\n1️⃣ Loading Knowledge Base...")
    loader = DocumentLoader(data_dir=settings.data_dir)
    knowledge_base = loader.load_all()
    print(f"   ✅ Loaded {len(knowledge_base.categories)} categories")
    
    print("\n2️⃣ Initializing AI Services...")
    classifier = RequestClassifier(settings.openai_api_key, settings.openai_model)
    print("   ✅ Request Classifier ready")
    
    retriever = KnowledgeRetriever(knowledge_base, settings.embedding_model)
    await retriever.initialize()
    print("   ✅ Knowledge Retriever ready")
    
    generator = ResponseGenerator(settings.openai_api_key, settings.openai_model)
    print("   ✅ Response Generator ready")
    
    escalator = EscalationManager(knowledge_base)
    print("   ✅ Escalation Manager ready")
    
    # Test cases
    test_cases = [
        "I forgot my password and can't log into my computer. How do I reset it?",
        "My laptop screen went completely black and won't turn on. I have an important presentation tomorrow.",
        "I think someone hacked my computer because I'm seeing strange pop-ups.",
        "I need to install Slack but it keeps giving me an error message.",
        "My email stopped syncing and I'm not receiving any new messages."
    ]
    
    print("\n3️⃣ Running Test Cases...")
    print("=" * 50)
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_message[:50]}...")
        
        try:
            # Step 1: Classification
            categories = list(knowledge_base.categories.keys())
            classification = await classifier.classify_request(test_message, categories)
            print(f"   📂 Category: {classification.category} (confidence: {classification.confidence:.2f})")
            
            # Step 2: Knowledge Retrieval
            knowledge_items = await retriever.retrieve_knowledge(
                test_message, classification.category, top_k=2
            )
            print(f"   📚 Retrieved {len(knowledge_items)} knowledge items")
            
            # Step 3: Escalation Check
            escalation = escalator.check_escalation(
                classification.category, test_message, classification.confidence
            )
            print(f"   🚨 Escalation required: {escalation.required}")
            
            # Step 4: Response Generation
            from models import HelpDeskRequest
            import uuid
            from datetime import datetime
            
            request = HelpDeskRequest(
                id=str(uuid.uuid4()),
                message=test_message,
                user_id="test.user@techcorp.com",
                priority="normal",
                timestamp=datetime.now(),
                category=classification.category,
                confidence=classification.confidence
            )
            
            response = await generator.generate_response(
                request, classification, knowledge_items, escalation
            )
            print(f"   ✍️  Response generated ({len(response)} characters)")
            print(f"   💬 Preview: {response[:100]}...")
            
            print(f"   ✅ Test Case {i} completed successfully!")
            
        except Exception as e:
            print(f"   ❌ Test Case {i} failed: {e}")
    
    print("\n🎉 Help Desk System Test Complete!")
    print("=" * 50)
    
    # Show system statistics
    print(f"\n📊 System Statistics:")
    print(f"   • Categories: {len(knowledge_base.categories)}")
    print(f"   • Installation Guides: {len(knowledge_base.installation_guides)}")
    print(f"   • Troubleshooting Procedures: {len(knowledge_base.troubleshooting_steps)}")
    print(f"   • Knowledge Chunks: {len(retriever.knowledge_chunks)}")


if __name__ == "__main__":
    # Check if .env file exists
    import os
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
        exit(1)
    
    # Run the test
    asyncio.run(test_help_desk_system())