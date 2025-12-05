"""
Main FastAPI application
"""
import logging
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import json

from core.config import get_settings
from models.user import User, UserRole
from models.agent import AgentCreate, AgentUpdate
from models.chat import ChatRequest
from services.authentication import AuthenticationService
from services.agent_service import AgentService
from services.document_service import DocumentService
from services.chat_service import ChatService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Vertex AI RAG Demo",
    description="RAG application with Vertex AI and Google Cloud",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
auth_service = AuthenticationService()
agent_service = AgentService()
document_service = DocumentService()
chat_service = ChatService()


# Dependency for authentication
async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Get current authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "")
    try:
        token_data = await auth_service.verify_token(token)
        user = await auth_service.get_or_create_user(
            token_data["uid"],
            token_data["email"],
            token_data.get("name")
        )
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication")


# Dependency for admin-only routes
async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vertex-rag-backend"}


# User routes
@app.get("/api/users/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user info"""
    return user


@app.get("/api/users")
async def list_users(admin: User = Depends(require_admin)):
    """List all users (admin only)"""
    return await auth_service.list_users()


@app.patch("/api/users/{user_id}/role")
async def update_user_role(user_id: str, role: UserRole, admin: User = Depends(require_admin)):
    """Update user role (admin only)"""
    return await auth_service.update_user_role(user_id, role)


# Agent routes
@app.post("/api/agents")
async def create_agent(agent_create: AgentCreate, admin: User = Depends(require_admin)):
    """Create new agent (admin only)"""
    return await agent_service.create_agent(agent_create, admin.id)


@app.get("/api/agents")
async def list_agents(user: User = Depends(get_current_user)):
    """List all agents"""
    return await agent_service.list_agents()


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str, user: User = Depends(get_current_user)):
    """Get agent details"""
    return await agent_service.get_agent(agent_id)


@app.patch("/api/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    admin: User = Depends(require_admin)
):
    """Update agent (admin only)"""
    return await agent_service.update_agent(agent_id, agent_update)


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str, admin: User = Depends(require_admin)):
    """Delete agent (admin only)"""
    await agent_service.delete_agent(agent_id)
    return {"message": "Agent deleted successfully"}


# Document routes
@app.post("/api/agents/{agent_id}/documents")
async def upload_documents(
    agent_id: str,
    files: list[UploadFile] = File(...),
    admin: User = Depends(require_admin)
):
    """Upload documents (admin only)"""
    results = []
    for file in files:
        try:
            doc = await document_service.upload_document(agent_id, file, admin.id)
            results.append(doc)
        except Exception as e:
            logger.error(f"Error uploading {file.filename}: {e}")
            results.append({"filename": file.filename, "error": str(e)})
    return results


@app.get("/api/agents/{agent_id}/documents")
async def list_documents(agent_id: str, user: User = Depends(get_current_user)):
    """List documents"""
    return await document_service.list_documents(agent_id)


@app.get("/api/agents/{agent_id}/documents/{doc_id}")
async def get_document(agent_id: str, doc_id: str, user: User = Depends(get_current_user)):
    """Get document details"""
    return await document_service.get_document(agent_id, doc_id)


@app.get("/api/agents/{agent_id}/documents/{doc_id}/download")
async def download_document(agent_id: str, doc_id: str, user: User = Depends(get_current_user)):
    """Get download URL"""
    url = await document_service.get_download_url(agent_id, doc_id)
    return {"downloadUrl": url}


@app.delete("/api/agents/{agent_id}/documents/{doc_id}")
async def delete_document(
    agent_id: str,
    doc_id: str,
    admin: User = Depends(require_admin)
):
    """Delete document (admin only)"""
    await document_service.delete_document(agent_id, doc_id)
    return {"message": "Document deleted successfully"}


# Chat routes
@app.post("/api/agents/{agent_id}/chat/stream")
async def chat_stream(
    agent_id: str,
    request: ChatRequest,
    user: User = Depends(get_current_user)
):
    """Chat with streaming (SSE)"""
    async def event_generator():
        async for chunk in chat_service.chat_stream(
            agent_id,
            request.message,
            user.id,
            request.conversation_id
        ):
            event_type = chunk["type"]
            data = chunk["data"]

            # Format as SSE
            yield f"event: {event_type}\n"
            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.delete("/api/agents/{agent_id}/chat/history")
async def clear_chat_history(agent_id: str, user: User = Depends(get_current_user)):
    """Clear chat history"""
    await chat_service.clear_history(agent_id, user.id)
    return {"message": "Chat history cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
