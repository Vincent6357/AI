"""Chat service for RAG conversations"""
import logging
import re
from typing import AsyncGenerator
from firebase_admin import firestore
from models.chat import Message, MessageRole, Citation, RetrievalContext
from services.vertex_ai_service import VertexAIService
from services.agent_service import AgentService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat operations"""

    def __init__(self):
        self.firestore_client = firestore.AsyncClient()
        self.vertex_service = VertexAIService()
        self.agent_service = AgentService()

    async def chat_stream(
        self,
        agent_id: str,
        user_message: str,
        user_id: str,
        conversation_id: str = None
    ) -> AsyncGenerator[dict, None]:
        """Stream chat response with RAG"""
        try:
            agent = await self.agent_service.get_agent(agent_id)

            # Get conversation history
            history = []
            if conversation_id:
                history = await self._get_conversation_history(agent_id, conversation_id)

            # Retrieve contexts
            contexts = await self.vertex_service.retrieve_contexts(
                agent.corpus_id,
                user_message,
                agent.settings.retrieval_top_k,
                agent.settings.similarity_threshold
            )

            # Yield retrieval info
            yield {
                "type": "retrieval",
                "data": [
                    {
                        "content": ctx["content"][:500],
                        "source": ctx["source"],
                        "score": ctx["score"],
                        "chunk_id": ctx.get("chunk_id")
                    }
                    for ctx in contexts
                ]
            }

            # Generate response with streaming
            full_response = ""
            async for chunk in self.vertex_service.chat_stream(
                agent, user_message, history, contexts
            ):
                full_response += chunk
                yield {"type": "content", "data": chunk}

            # Extract citations
            citations = self._extract_citations(full_response, contexts)
            yield {"type": "citations", "data": citations}

            # Save messages
            await self._save_messages(
                agent_id,
                user_id,
                conversation_id or user_id,
                user_message,
                full_response,
                citations
            )

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield {"type": "error", "data": str(e)}

    async def _get_conversation_history(self, agent_id: str, conversation_id: str) -> list[dict]:
        """Get conversation history"""
        messages = []
        async for msg_doc in self.firestore_client.collection("agents").document(agent_id)\
                .collection("conversations").document(conversation_id)\
                .collection("messages").order_by("timestamp").limit(20).stream():
            msg_data = msg_doc.to_dict()
            messages.append({
                "role": msg_data["role"],
                "content": msg_data["content"]
            })
        return messages

    def _extract_citations(self, response: str, contexts: list[dict]) -> list[dict]:
        """Extract citations from response"""
        citations = []
        pattern = r'\[Source:\s*([^\]]+)\]'
        matches = re.findall(pattern, response)

        for match in matches:
            for ctx in contexts:
                if match.lower() in ctx["source"].lower():
                    citations.append({
                        "source": ctx["source"],
                        "chunk_id": ctx.get("chunk_id"),
                        "snippet": ctx["content"][:200]
                    })
                    break

        return citations

    async def _save_messages(
        self,
        agent_id: str,
        user_id: str,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        citations: list
    ):
        """Save messages to Firestore"""
        conv_ref = self.firestore_client.collection("agents").document(agent_id)\
            .collection("conversations").document(conversation_id)

        await conv_ref.set({
            "userId": user_id,
            "lastMessageAt": firestore.SERVER_TIMESTAMP,
        }, merge=True)

        messages_ref = conv_ref.collection("messages")
        await messages_ref.add({
            "role": "user",
            "content": user_message,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        await messages_ref.add({
            "role": "assistant",
            "content": assistant_response,
            "citations": citations,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

    async def clear_history(self, agent_id: str, user_id: str):
        """Clear conversation history"""
        conv_ref = self.firestore_client.collection("agents").document(agent_id)\
            .collection("conversations").document(user_id)
        await conv_ref.delete()
