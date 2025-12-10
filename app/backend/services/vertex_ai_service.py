"""
Vertex AI service for chat and embeddings
"""
import logging
from typing import AsyncGenerator, Optional
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part
from google.cloud import aiplatform

# RAG API is optional - may not be available in all vertexai versions
try:
    from vertexai.preview import rag
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    rag = None
    logging.warning("vertexai.preview.rag not available - RAG features will be disabled")

from core.config import get_settings
from models.agent import Agent

logger = logging.getLogger(__name__)
settings = get_settings()


class VertexAIService:
    """Service for Vertex AI operations"""

    def __init__(self):
        """Initialize Vertex AI - lazy initialization"""
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Vertex AI"""
        if self._initialized:
            return
        try:
            vertexai.init(
                project=settings.GCP_PROJECT_ID,
                location=settings.VERTEX_AI_LOCATION
            )
            self._initialized = True
            logger.info("Vertex AI initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise

    async def chat_stream(
        self,
        agent: Agent,
        message: str,
        conversation_history: list[dict],
        retrieved_contexts: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response using Gemini

        Args:
            agent: Agent configuration
            message: User message
            conversation_history: Previous messages
            retrieved_contexts: Retrieved contexts from RAG

        Yields:
            Response chunks
        """
        self._ensure_initialized()
        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(agent, retrieved_contexts)

            # Initialize model
            model = GenerativeModel(
                model_name=agent.settings.model,
                system_instruction=system_prompt
            )

            # Build conversation
            contents = self._build_contents(conversation_history, message)

            # Generate with streaming
            response = model.generate_content(
                contents,
                generation_config={
                    "temperature": agent.settings.temperature,
                    "max_output_tokens": agent.settings.max_tokens,
                },
                stream=True
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            raise

    def _build_system_prompt(self, agent: Agent, contexts: Optional[list] = None) -> str:
        """Build system prompt with retrieved context"""
        base_prompt = agent.settings.system_prompt or """Tu es un assistant intelligent qui répond aux questions en te basant sur les documents fournis.
Réponds de manière précise et cite tes sources quand c'est pertinent en utilisant le format [Source: nom_du_fichier].
Si l'information n'est pas dans les documents, dis-le clairement."""

        if contexts:
            context_text = "\n\n".join([
                f"[Source: {ctx.get('source', 'Unknown')}]\n{ctx.get('content', '')}"
                for ctx in contexts
            ])
            return f"""{base_prompt}

DOCUMENTS DE RÉFÉRENCE:
{context_text}

INSTRUCTIONS:
- Base tes réponses uniquement sur les documents ci-dessus
- Cite les sources pertinentes avec [Source: nom_du_fichier]
- Si tu ne trouves pas l'information, indique-le clairement
- Réponds dans la même langue que la question"""

        return base_prompt

    def _build_contents(self, history: list[dict], current_message: str) -> list:
        """Build conversation contents for Gemini"""
        contents = []

        for msg in history[-10:]:  # Keep last 10 messages
            contents.append(Content(
                role="user" if msg["role"] == "user" else "model",
                parts=[Part.from_text(msg["content"])]
            ))

        contents.append(Content(
            role="user",
            parts=[Part.from_text(current_message)]
        ))

        return contents

    async def create_rag_corpus(self, agent_id: str, name: str) -> str:
        """
        Create a RAG corpus

        Args:
            agent_id: Agent ID
            name: Corpus name

        Returns:
            Corpus ID
        """
        self._ensure_initialized()
        if not RAG_AVAILABLE:
            logger.warning("RAG API not available, skipping corpus creation")
            return f"mock-corpus-{agent_id}"

        try:
            corpus = rag.create_corpus(
                display_name=f"agent-{agent_id}-{name}",
                description=f"Knowledge base for agent {name}"
            )
            return corpus.name
        except Exception as e:
            logger.error(f"Error creating RAG corpus: {e}")
            raise

    async def import_files_to_corpus(
        self,
        corpus_id: str,
        gcs_paths: list[str],
        chunk_size: int = 1024,
        chunk_overlap: int = 200
    ):
        """
        Import files to RAG corpus

        Args:
            corpus_id: Corpus ID
            gcs_paths: List of GCS file paths
            chunk_size: Chunk size for splitting
            chunk_overlap: Overlap between chunks
        """
        self._ensure_initialized()
        if not RAG_AVAILABLE:
            logger.warning("RAG API not available, skipping file import")
            return

        try:
            rag.import_files(
                corpus_name=corpus_id,
                paths=gcs_paths,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        except Exception as e:
            logger.error(f"Error importing files to corpus: {e}")
            raise

    async def retrieve_contexts(
        self,
        corpus_id: str,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> list[dict]:
        """
        Retrieve relevant contexts from RAG corpus

        Args:
            corpus_id: Corpus ID
            query: Query text
            top_k: Number of results
            threshold: Similarity threshold

        Returns:
            List of context dicts
        """
        self._ensure_initialized()
        if not RAG_AVAILABLE:
            logger.warning("RAG API not available, returning empty contexts")
            return []

        try:
            response = rag.retrieval_query(
                rag_resources=[
                    rag.RagResource(rag_corpus=corpus_id)
                ],
                text=query,
                similarity_top_k=top_k,
                vector_distance_threshold=threshold,
            )

            contexts = []
            for ctx in response.contexts:
                contexts.append({
                    "content": ctx.text,
                    "source": ctx.source_name,
                    "score": ctx.score,
                    "chunk_id": getattr(ctx, "chunk_id", None)
                })

            return contexts

        except Exception as e:
            logger.error(f"Error retrieving contexts: {e}")
            return []
