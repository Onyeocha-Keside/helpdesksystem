import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings, Settings
from models import UserRequest, HelpDeskRequest, HelpDeskResponse
from utils import DocumentLoader, KnowledgeBase
from services.classifier import RequestClassifier
from services.retriever import KnowledgeRetriever
from services.generator import ResponseGenerator
from services.escalator import EscalationManager


# Global variables for shared resources
knowledge_base: KnowledgeBase = None
classifier: RequestClassifier = None
retriever: KnowledgeRetriever = None
generator: ResponseGenerator = None
escalator: EscalationManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    print("🚀 Starting Intelligent Help Desk System...")
    
    global knowledge_base, classifier, retriever, generator, escalator
    settings = get_settings()
    
    try:
        # Load knowledge base
        print("📚 Loading knowledge base...")
        loader = DocumentLoader(data_dir=settings.data_dir)
        knowledge_base = loader.load_all()
        
        # Initialize services
        print("🤖 Initializing AI services...")
        classifier = RequestClassifier(settings.openai_api_key, settings.openai_model)
        
        print("🔍 Setting up knowledge retrieval...")
        retriever = KnowledgeRetriever(knowledge_base, settings.embedding_model)
        await retriever.initialize()  # Build embeddings
        
        print("✍️ Initializing response generator...")
        generator = ResponseGenerator(settings.openai_api_key, settings.openai_model)
        
        print("🚨 Setting up escalation manager...")
        escalator = EscalationManager(knowledge_base)
        
        print("✅ Help Desk System ready!")
        
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Help Desk System...")


# Create FastAPI app
app = FastAPI(
    title="Intelligent Help Desk System",
    description="AI-powered help desk system with request classification, knowledge retrieval, and automated responses",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get settings
def get_app_settings() -> Settings:
    return get_settings()


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": "Intelligent Help Desk System",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "submit_request": "/request",
            "categories": "/categories",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global knowledge_base, classifier, retriever, generator, escalator
    
    status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "knowledge_base": knowledge_base is not None,
            "classifier": classifier is not None,
            "retriever": retriever is not None,
            "generator": generator is not None,
            "escalator": escalator is not None
        }
    }
    
    # Check if all components are loaded
    all_healthy = all(status["components"].values())
    if not all_healthy:
        status["status"] = "unhealthy"
        return JSONResponse(
            status_code=503,
            content=status
        )
    
    return status


@app.get("/categories")
async def get_categories():
    """Get all available help desk categories."""
    global knowledge_base
    
    if not knowledge_base:
        raise HTTPException(status_code=503, detail="Knowledge base not loaded")
    
    categories = {}
    for name, category in knowledge_base.categories.items():
        categories[name] = {
            "description": category.description,
            "typical_resolution_time": category.typical_resolution_time,
            "escalation_triggers": category.escalation_triggers
        }
    
    return {
        "categories": categories,
        "total_categories": len(categories)
    }


@app.post("/request", response_model=HelpDeskResponse)
async def submit_request(
    user_request: UserRequest,
    settings: Settings = Depends(get_app_settings)
):
    """Process a help desk request."""
    global knowledge_base, classifier, retriever, generator, escalator
    
    # Check if all services are available
    if not all([knowledge_base, classifier, retriever, generator, escalator]):
        raise HTTPException(
            status_code=503, 
            detail="Help desk services not fully initialized"
        )
    
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Create internal request object
        help_request = HelpDeskRequest(
            id=request_id,
            message=user_request.message,
            user_id=user_request.user_id,
            priority=user_request.priority
        )
        
        # Step 1: Classify the request
        print(f"🔍 Classifying request {request_id}")
        classification_result = await classifier.classify_request(
            help_request.message,
            list(knowledge_base.categories.keys())
        )
        
        # Update request with classification
        help_request.category = classification_result.category
        help_request.confidence = classification_result.confidence
        
        # Step 2: Retrieve relevant knowledge
        print(f"📖 Retrieving knowledge for {classification_result.category}")
        knowledge_items = await retriever.retrieve_knowledge(
            help_request.message,
            classification_result.category,
            top_k=3
        )
        
        # Step 3: Check escalation requirements
        print(f"🚨 Checking escalation requirements")
        escalation_info = escalator.check_escalation(
            classification_result.category,
            help_request.message,
            classification_result.confidence
        )
        
        # Step 4: Generate response
        print(f"✍️ Generating response")
        response_text = await generator.generate_response(
            help_request,
            classification_result,
            knowledge_items,
            escalation_info
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create final response
        response = HelpDeskResponse(
            request_id=request_id,
            category=classification_result.category,
            response=response_text,
            classification=classification_result,
            knowledge_items=knowledge_items,
            escalation=escalation_info,
            processing_time=processing_time
        )
        
        print(f"✅ Request {request_id} processed in {processing_time:.2f}s")
        return response
        
    except Exception as e:
        print(f"❌ Error processing request {request_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request: {str(e)}"
        )


@app.get("/stats")
async def get_system_stats():
    """Get system statistics."""
    global knowledge_base
    
    if not knowledge_base:
        raise HTTPException(status_code=503, detail="Knowledge base not loaded")
    
    return {
        "knowledge_base": {
            "categories": len(knowledge_base.categories),
            "installation_guides": len(knowledge_base.installation_guides),
            "troubleshooting_procedures": len(knowledge_base.troubleshooting_steps),
            "documents": len(knowledge_base.documents)
        },
        "categories": list(knowledge_base.categories.keys())
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )