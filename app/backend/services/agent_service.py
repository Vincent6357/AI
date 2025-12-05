"""Agent service for multi-tenant management"""
import logging
import uuid
from datetime import datetime
from firebase_admin import firestore
from models.agent import Agent, AgentCreate, AgentUpdate, AgentStatus, AgentSettings
from services.storage_service import StorageService
from services.vertex_ai_service import VertexAIService
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentService:
    """Service for agent management"""

    def __init__(self):
        self.firestore_client = firestore.AsyncClient()
        self.storage_service = StorageService()
        self.vertex_service = VertexAIService()

    async def create_agent(self, agent_create: AgentCreate, created_by: str) -> Agent:
        """Create a new agent"""
        agent_id = str(uuid.uuid4())[:8]
        bucket_name = f"{settings.GCP_PROJECT_ID}-agent-{agent_id}"

        # Create GCS bucket
        self.storage_service.create_bucket(bucket_name)

        # Create RAG corpus
        corpus_id = await self.vertex_service.create_rag_corpus(agent_id, agent_create.name)

        # Create agent in Firestore
        agent_data = {
            "id": agent_id,
            "name": agent_create.name,
            "description": agent_create.description,
            "createdBy": created_by,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "bucketName": bucket_name,
            "corpusId": corpus_id,
            "dataStoreId": None,
            "status": AgentStatus.ACTIVE.value,
            "settings": AgentSettings().dict(),
            "documentCount": 0
        }

        await self.firestore_client.collection("agents").document(agent_id).set(agent_data)

        return Agent(**agent_data, created_at=datetime.utcnow(), updated_at=datetime.utcnow())

    async def get_agent(self, agent_id: str) -> Agent:
        """Get agent by ID"""
        doc = await self.firestore_client.collection("agents").document(agent_id).get()
        if not doc.exists:
            raise ValueError(f"Agent {agent_id} not found")
        return Agent(**doc.to_dict())

    async def list_agents(self) -> list[Agent]:
        """List all agents"""
        agents = []
        async for doc in self.firestore_client.collection("agents").stream():
            agents.append(Agent(**doc.to_dict()))
        return agents

    async def update_agent(self, agent_id: str, agent_update: AgentUpdate) -> Agent:
        """Update agent"""
        update_data = agent_update.dict(exclude_none=True)
        update_data["updatedAt"] = firestore.SERVER_TIMESTAMP

        await self.firestore_client.collection("agents").document(agent_id).update(update_data)
        return await self.get_agent(agent_id)

    async def delete_agent(self, agent_id: str):
        """Delete agent and all resources"""
        agent = await self.get_agent(agent_id)

        # Delete bucket
        self.storage_service.delete_bucket(agent.bucket_name, force=True)

        # Delete from Firestore
        await self.firestore_client.collection("agents").document(agent_id).delete()
