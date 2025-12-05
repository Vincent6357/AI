"""Document service for file management"""
import logging
import uuid
import hashlib
from pathlib import Path
from firebase_admin import firestore
from fastapi import UploadFile
from models.document import Document, DocumentCreate, DocumentStatus
from services.storage_service import StorageService
from services.vertex_ai_service import VertexAIService
from services.agent_service import AgentService
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentService:
    """Service for document management"""

    MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS

    def __init__(self):
        self.firestore_client = firestore.AsyncClient()
        self.storage_service = StorageService()
        self.vertex_service = VertexAIService()
        self.agent_service = AgentService()

    async def upload_document(self, agent_id: str, file: UploadFile, uploaded_by: str) -> Document:
        """Upload document"""
        # Validate file
        ext = Path(file.filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type not supported: {ext}")

        content = await file.read()
        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")

        # Get agent
        agent = await self.agent_service.get_agent(agent_id)

        # Generate filename
        file_hash = hashlib.md5(content).hexdigest()[:8]
        safe_filename = f"{file_hash}_{file.filename}"
        gcs_path = f"documents/{safe_filename}"

        # Upload to GCS
        full_gcs_path = self.storage_service.upload_file(
            agent.bucket_name,
            content,
            gcs_path,
            file.content_type
        )

        # Create document record
        doc_id = str(uuid.uuid4())
        doc_data = {
            "id": doc_id,
            "agentId": agent_id,
            "fileName": safe_filename,
            "originalName": file.filename,
            "gcsPath": full_gcs_path,
            "contentType": file.content_type,
            "size": len(content),
            "uploadedBy": uploaded_by,
            "uploadedAt": firestore.SERVER_TIMESTAMP,
            "status": DocumentStatus.UPLOADED.value,
            "chunksCount": 0
        }

        await self.firestore_client.collection("agents").document(agent_id)\
            .collection("documents").document(doc_id).set(doc_data)

        # Trigger indexing (async)
        await self._index_document(agent_id, doc_id)

        return Document(**doc_data)

    async def _index_document(self, agent_id: str, doc_id: str):
        """Index document in Vertex AI RAG"""
        try:
            agent = await self.agent_service.get_agent(agent_id)
            doc = await self.get_document(agent_id, doc_id)

            # Update status to processing
            await self.firestore_client.collection("agents").document(agent_id)\
                .collection("documents").document(doc_id)\
                .update({"status": DocumentStatus.PROCESSING.value})

            # Import to RAG corpus
            await self.vertex_service.import_files_to_corpus(
                agent.corpus_id,
                [doc.gcs_path]
            )

            # Update status to indexed
            await self.firestore_client.collection("agents").document(agent_id)\
                .collection("documents").document(doc_id)\
                .update({"status": DocumentStatus.INDEXED.value})

        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            await self.firestore_client.collection("agents").document(agent_id)\
                .collection("documents").document(doc_id)\
                .update({"status": DocumentStatus.ERROR.value, "errorMessage": str(e)})

    async def get_document(self, agent_id: str, doc_id: str) -> Document:
        """Get document by ID"""
        doc = await self.firestore_client.collection("agents").document(agent_id)\
            .collection("documents").document(doc_id).get()
        if not doc.exists:
            raise ValueError(f"Document {doc_id} not found")
        return Document(**doc.to_dict())

    async def list_documents(self, agent_id: str) -> list[Document]:
        """List documents for agent"""
        documents = []
        async for doc in self.firestore_client.collection("agents").document(agent_id)\
                .collection("documents").stream():
            documents.append(Document(**doc.to_dict()))
        return documents

    async def delete_document(self, agent_id: str, doc_id: str):
        """Delete document"""
        agent = await self.agent_service.get_agent(agent_id)
        doc = await self.get_document(agent_id, doc_id)

        # Delete from GCS
        blob_name = doc.gcs_path.replace(f"gs://{agent.bucket_name}/", "")
        self.storage_service.delete_file(agent.bucket_name, blob_name)

        # Delete from Firestore
        await self.firestore_client.collection("agents").document(agent_id)\
            .collection("documents").document(doc_id).delete()

    async def get_download_url(self, agent_id: str, doc_id: str) -> str:
        """Generate download URL"""
        agent = await self.agent_service.get_agent(agent_id)
        doc = await self.get_document(agent_id, doc_id)

        blob_name = doc.gcs_path.replace(f"gs://{agent.bucket_name}/", "")
        return self.storage_service.generate_signed_url(agent.bucket_name, blob_name)
