"""
Main FastAPI application
"""
import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Any
import json
import uuid

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
logger.info("=" * 50)
logger.info("Starting Vertex AI RAG Backend...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info("=" * 50)

# Import configuration
try:
    from core.config import get_settings
    logger.info("Configuration module loaded")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise

# Import models
try:
    from models.user import User, UserRole
    from models.agent import AgentCreate, AgentUpdate
    from models.chat import ChatRequest
    logger.info("Models loaded")
except Exception as e:
    logger.error(f"Failed to load models: {e}")
    raise

# Import services - these use lazy initialization
try:
    from services.authentication import AuthenticationService
    from services.agent_service import AgentService
    from services.document_service import DocumentService
    from services.chat_service import ChatService
    from services.vertex_ai_service import VertexAIService
    logger.info("Services modules loaded (lazy init)")
except Exception as e:
    logger.error(f"Failed to load services: {e}")
    raise

# Initialize settings
settings = get_settings()
logger.info(f"Settings loaded - Project: {settings.GCP_PROJECT_ID or 'NOT SET'}")

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

# Initialize services (lazy - no GCP calls at startup)
logger.info("Creating service instances (lazy initialization)...")
auth_service = AuthenticationService()
agent_service = AgentService()
document_service = DocumentService()
chat_service = ChatService()
vertex_ai_service = VertexAIService()
logger.info("All service instances created successfully")
logger.info("=" * 50)
logger.info("Backend ready to accept requests!")
logger.info("=" * 50)


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


# Health check - must return quickly for Cloud Run
@app.get("/health")
async def health_check():
    """Health check endpoint - returns immediately without initializing services"""
    return {
        "status": "healthy",
        "service": "vertex-rag-backend",
        "project": settings.GCP_PROJECT_ID or "not-configured"
    }


# Startup check - more detailed status
@app.get("/startup")
async def startup_check():
    """Detailed startup check - use for debugging"""
    return {
        "status": "ready",
        "gcp_project": settings.GCP_PROJECT_ID or "NOT SET",
        "region": settings.GCP_REGION,
        "vertex_location": settings.VERTEX_AI_LOCATION,
        "use_login": settings.USE_LOGIN,
        "microsoft_oauth": bool(settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_TENANT_ID),
    }


# Debug endpoint to check configuration
@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration status"""
    return {
        "gcp_project_id": bool(settings.GCP_PROJECT_ID),
        "gcp_project_id_value": settings.GCP_PROJECT_ID[:10] + "..." if settings.GCP_PROJECT_ID else None,
        "gcp_region": settings.GCP_REGION,
        "vertex_ai_location": settings.VERTEX_AI_LOCATION,
        "vertex_ai_service_initialized": vertex_ai_service is not None,
        "default_model": settings.DEFAULT_MODEL,
        "microsoft_client_id_configured": bool(settings.MICROSOFT_CLIENT_ID),
        "microsoft_tenant_id_configured": bool(settings.MICROSOFT_TENANT_ID),
        "firebase_api_key_configured": bool(settings.FIREBASE_API_KEY),
        "firebase_project_id": settings.FIREBASE_PROJECT_ID,
        "use_login": settings.USE_LOGIN,
        "main_bucket": settings.MAIN_BUCKET_NAME,
        "cors_origins": settings.CORS_ORIGINS,
    }


# Auth setup endpoint - required by frontend for MSAL configuration
@app.get("/auth_setup")
async def auth_setup():
    """Return authentication configuration for the frontend"""
    # Build MSAL configuration
    authority = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}" if settings.MICROSOFT_TENANT_ID else ""

    # Only enable login if both USE_LOGIN is true AND Microsoft OAuth is properly configured
    microsoft_oauth_configured = bool(settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_TENANT_ID)
    use_login_effective = settings.USE_LOGIN and microsoft_oauth_configured

    if settings.USE_LOGIN and not microsoft_oauth_configured:
        logger.warning(
            "USE_LOGIN is enabled but Microsoft OAuth credentials are not configured. "
            "Please set MICROSOFT_CLIENT_ID and MICROSOFT_TENANT_ID environment variables. "
            "Login button will be disabled."
        )

    return {
        "useLogin": use_login_effective,
        "requireAccessControl": settings.REQUIRE_ACCESS_CONTROL,
        "enableUnauthenticatedAccess": settings.ENABLE_UNAUTHENTICATED_ACCESS,
        "msalConfig": {
            "auth": {
                "clientId": settings.MICROSOFT_CLIENT_ID,
                "authority": authority,
                "redirectUri": "/",
                "postLogoutRedirectUri": "/",
                "navigateToLoginRequestUrl": True
            },
            "cache": {
                "cacheLocation": "sessionStorage",
                "storeAuthStateInCookie": False
            }
        },
        "loginRequest": {
            "scopes": [".default"]
        },
        "tokenRequest": {
            "scopes": [f"api://{settings.MICROSOFT_CLIENT_ID}/.default"] if settings.MICROSOFT_CLIENT_ID else []
        }
    }


# Config endpoint - return app configuration
@app.get("/config")
async def get_config():
    """Return application configuration"""
    return {
        "defaultReasoningEffort": "medium",
        "defaultRetrievalReasoningEffort": "medium",
        "showMultimodalOptions": False,
        "showSemanticRankerOption": False,
        "showQueryRewritingOption": False,
        "showReasoningEffortOption": False,
        "streamingEnabled": True,
        "showVectorOption": True,
        "showUserUpload": True,
        "showLanguagePicker": False,
        "showSpeechInput": False,
        "showSpeechOutputBrowser": False,
        "showSpeechOutputAzure": False,
        "showChatHistoryBrowser": True,
        "showChatHistoryCosmos": False,
        "showAgenticRetrievalOption": False,
        "ragSearchTextEmbeddings": True,
        "ragSearchImageEmbeddings": False,
        "ragSendTextSources": True,
        "ragSendImageSources": False,
        "webSourceEnabled": False,
        "sharepointSourceEnabled": False
    }


# .auth/me endpoint - Azure App Services authentication pattern
@app.get("/.auth/me")
async def auth_me():
    """Return empty array for unauthenticated users (Azure App Services pattern)"""
    return []


# Frontend-compatible chat endpoints

def create_chat_response(content: str, session_state: Any = None):
    """Create a response in the format expected by the frontend"""
    return {
        "message": {"content": content, "role": "assistant"},
        "delta": {"content": "", "role": "assistant"},
        "context": {
            "data_points": {
                "text": [],
                "images": [],
                "citations": [],
                "citation_activity_details": {},
                "external_results_metadata": []
            },
            "followup_questions": None,
            "thoughts": []
        },
        "session_state": session_state or str(uuid.uuid4())
    }


@app.post("/ask")
async def ask_endpoint(request: Request):
    """Ask endpoint - single question/answer"""
    try:
        body = await request.json()
        messages = body.get("messages", [])

        if not messages:
            return create_chat_response("No message provided")

        # Get the last user message
        user_message = messages[-1].get("content", "") if messages else ""

        # Use Vertex AI if available
        if vertex_ai_service and settings.GCP_PROJECT_ID:
            try:
                from vertexai.generative_models import GenerativeModel

                model = GenerativeModel(
                    model_name=settings.DEFAULT_MODEL,
                    system_instruction="Tu es un assistant intelligent. Réponds de manière précise et utile en français."
                )

                response = model.generate_content(
                    user_message,
                    generation_config={
                        "temperature": settings.DEFAULT_TEMPERATURE,
                        "max_output_tokens": settings.DEFAULT_MAX_TOKENS,
                    }
                )

                response_content = response.text
            except Exception as e:
                logger.error(f"Vertex AI error: {e}")
                response_content = f"Erreur lors de la génération de la réponse: {str(e)}"
        else:
            response_content = "Le service Vertex AI n'est pas configuré. Veuillez vérifier la configuration GCP."

        return create_chat_response(response_content, body.get("session_state"))

    except Exception as e:
        logger.error(f"Error in /ask: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/chat")
async def chat_endpoint(request: Request):
    """Chat endpoint - non-streaming"""
    try:
        body = await request.json()
        messages = body.get("messages", [])

        if not messages:
            return create_chat_response("No message provided")

        user_message = messages[-1].get("content", "") if messages else ""

        # Use Vertex AI if available
        if vertex_ai_service and settings.GCP_PROJECT_ID:
            try:
                from vertexai.generative_models import GenerativeModel, Content, Part

                model = GenerativeModel(
                    model_name=settings.DEFAULT_MODEL,
                    system_instruction="Tu es un assistant intelligent. Réponds de manière précise et utile en français."
                )

                # Build conversation history
                contents = []
                for msg in messages[:-1]:  # All messages except the last
                    role = "user" if msg.get("role") == "user" else "model"
                    contents.append(Content(
                        role=role,
                        parts=[Part.from_text(msg.get("content", ""))]
                    ))

                # Add current message
                contents.append(Content(
                    role="user",
                    parts=[Part.from_text(user_message)]
                ))

                response = model.generate_content(
                    contents,
                    generation_config={
                        "temperature": settings.DEFAULT_TEMPERATURE,
                        "max_output_tokens": settings.DEFAULT_MAX_TOKENS,
                    }
                )

                response_content = response.text
            except Exception as e:
                logger.error(f"Vertex AI error: {e}")
                response_content = f"Erreur lors de la génération de la réponse: {str(e)}"
        else:
            response_content = "Le service Vertex AI n'est pas configuré. Veuillez vérifier la configuration GCP."

        return create_chat_response(response_content, body.get("session_state"))

    except Exception as e:
        logger.error(f"Error in /chat: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/chat/stream")
async def chat_stream_endpoint(request: Request):
    """Chat streaming endpoint - Server-Sent Events"""
    try:
        body = await request.json()
        messages = body.get("messages", [])
        session_state = body.get("session_state") or str(uuid.uuid4())

        user_message = messages[-1].get("content", "") if messages else ""

        async def generate_stream():
            full_response = ""

            # Use Vertex AI if available
            if vertex_ai_service and settings.GCP_PROJECT_ID:
                try:
                    from vertexai.generative_models import GenerativeModel, Content, Part

                    model = GenerativeModel(
                        model_name=settings.DEFAULT_MODEL,
                        system_instruction="Tu es un assistant intelligent. Réponds de manière précise et utile en français."
                    )

                    # Build conversation history
                    contents = []
                    for msg in messages[:-1]:
                        role = "user" if msg.get("role") == "user" else "model"
                        contents.append(Content(
                            role=role,
                            parts=[Part.from_text(msg.get("content", ""))]
                        ))

                    contents.append(Content(
                        role="user",
                        parts=[Part.from_text(user_message)]
                    ))

                    # Stream response from Vertex AI
                    response = model.generate_content(
                        contents,
                        generation_config={
                            "temperature": settings.DEFAULT_TEMPERATURE,
                            "max_output_tokens": settings.DEFAULT_MAX_TOKENS,
                        },
                        stream=True
                    )

                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            yield json.dumps({
                                "delta": {"content": chunk.text, "role": "assistant"},
                                "context": {
                                    "data_points": {"text": [], "images": [], "citations": []},
                                    "followup_questions": None,
                                    "thoughts": []
                                },
                                "session_state": session_state
                            }) + "\n"

                except Exception as e:
                    logger.error(f"Vertex AI streaming error: {e}")
                    full_response = f"Erreur lors de la génération de la réponse: {str(e)}"
                    yield json.dumps({
                        "delta": {"content": full_response, "role": "assistant"},
                        "context": {
                            "data_points": {"text": [], "images": [], "citations": []},
                            "followup_questions": None,
                            "thoughts": []
                        },
                        "session_state": session_state
                    }) + "\n"
            else:
                full_response = "Le service Vertex AI n'est pas configuré. Veuillez vérifier la configuration GCP."
                yield json.dumps({
                    "delta": {"content": full_response, "role": "assistant"},
                    "context": {
                        "data_points": {"text": [], "images": [], "citations": []},
                        "followup_questions": None,
                        "thoughts": []
                    },
                    "session_state": session_state
                }) + "\n"

            # Send final message
            yield json.dumps({
                "message": {"content": full_response, "role": "assistant"},
                "delta": {"content": "", "role": "assistant"},
                "context": {
                    "data_points": {
                        "text": [],
                        "images": [],
                        "citations": [],
                        "citation_activity_details": {},
                        "external_results_metadata": []
                    },
                    "followup_questions": None,
                    "thoughts": []
                },
                "session_state": session_state
            }) + "\n"

        return StreamingResponse(
            generate_stream(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"Error in /chat/stream: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/speech")
async def speech_endpoint():
    """Speech synthesis endpoint - returns 400 as not enabled"""
    return JSONResponse(
        status_code=400,
        content={"message": "Speech synthesis is not enabled"}
    )


@app.post("/upload")
async def upload_endpoint(file: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """Upload file endpoint"""
    # TODO: Implement file upload to Cloud Storage
    return {"message": f"File '{file.filename}' upload endpoint. Implementation pending."}


@app.post("/delete_uploaded")
async def delete_uploaded_endpoint(request: Request, authorization: Optional[str] = Header(None)):
    """Delete uploaded file endpoint"""
    body = await request.json()
    filename = body.get("filename", "")
    return {"message": f"Delete endpoint for '{filename}'. Implementation pending."}


@app.get("/list_uploaded")
async def list_uploaded_endpoint(authorization: Optional[str] = Header(None)):
    """List uploaded files endpoint"""
    # TODO: List files from Cloud Storage
    return []


@app.post("/chat_history")
async def post_chat_history(request: Request, authorization: Optional[str] = Header(None)):
    """Save chat history"""
    body = await request.json()
    return {"id": str(uuid.uuid4()), "message": "Chat history saved"}


@app.get("/chat_history/sessions")
async def get_chat_history_list(
    count: int = 10,
    continuationToken: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Get chat history list"""
    return {"sessions": [], "continuation_token": None}


@app.get("/chat_history/sessions/{session_id}")
async def get_chat_history(session_id: str, authorization: Optional[str] = Header(None)):
    """Get specific chat history session"""
    return {"id": session_id, "entra_oid": "", "answers": []}


@app.delete("/chat_history/sessions/{session_id}")
async def delete_chat_history(session_id: str, authorization: Optional[str] = Header(None)):
    """Delete chat history session"""
    return {"message": "Deleted"}


@app.get("/content/{path:path}")
async def get_content(path: str, authorization: Optional[str] = Header(None)):
    """Get content/citations endpoint"""
    # TODO: Implement content retrieval from Cloud Storage
    return JSONResponse(
        status_code=404,
        content={"message": f"Content '{path}' not found"}
    )


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
