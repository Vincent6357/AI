"""
Authentication service using Firebase Authentication
"""
import logging
from typing import Optional
from datetime import datetime

import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore_v1 import AsyncClient

from models.user import User, UserCreate, UserRole
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthenticationService:
    """Service for user authentication and authorization"""

    def __init__(self):
        """Initialize Firebase Admin SDK"""
        if not firebase_admin._apps:
            # Initialize with default credentials in Cloud Run
            firebase_admin.initialize_app()

        self.firestore_client = firestore.AsyncClient()

    async def verify_token(self, token: str) -> dict:
        """
        Verify Firebase ID token and return user claims

        Args:
            token: Firebase ID token from client

        Returns:
            Dict with user claims

        Raises:
            ValueError: If token is invalid
        """
        try:
            decoded = auth.verify_id_token(token)
            return {
                "uid": decoded["uid"],
                "email": decoded.get("email"),
                "email_verified": decoded.get("email_verified", False),
                "provider": decoded.get("firebase", {}).get("sign_in_provider"),
                "claims": decoded,
            }
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(f"Invalid authentication token: {e}")

    async def get_or_create_user(self, firebase_uid: str, email: str, display_name: Optional[str] = None) -> User:
        """
        Get existing user or create new one

        Args:
            firebase_uid: Firebase UID
            email: User email
            display_name: Optional display name

        Returns:
            User object
        """
        # Check if user exists
        user_ref = self.firestore_client.collection("users").document(firebase_uid)
        user_doc = await user_ref.get()

        if user_doc.exists:
            # Update last login
            await user_ref.update({"lastLogin": firestore.SERVER_TIMESTAMP})
            user_data = user_doc.to_dict()
            return User(
                id=firebase_uid,
                email=user_data["email"],
                role=UserRole(user_data.get("role", "user")),
                firebase_uid=firebase_uid,
                microsoft_id=user_data.get("microsoftId"),
                display_name=user_data.get("displayName"),
                photo_url=user_data.get("photoUrl"),
                created_at=user_data["createdAt"],
                last_login=datetime.utcnow(),
            )
        else:
            # Create new user
            # First user is automatically admin
            users_count = len([u async for u in self.firestore_client.collection("users").limit(1).stream()])
            role = UserRole.ADMIN if users_count == 0 else UserRole.USER

            user_data = {
                "email": email,
                "role": role.value,
                "firebaseUid": firebase_uid,
                "displayName": display_name,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "lastLogin": firestore.SERVER_TIMESTAMP,
            }

            await user_ref.set(user_data)

            logger.info(f"Created new user: {email} with role: {role.value}")

            return User(
                id=firebase_uid,
                email=email,
                role=role,
                firebase_uid=firebase_uid,
                display_name=display_name,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
            )

    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User ID (Firebase UID)

        Returns:
            User object or None
        """
        user_ref = self.firestore_client.collection("users").document(user_id)
        user_doc = await user_ref.get()

        if not user_doc.exists:
            return None

        user_data = user_doc.to_dict()
        return User(
            id=user_id,
            email=user_data["email"],
            role=UserRole(user_data.get("role", "user")),
            firebase_uid=user_data["firebaseUid"],
            microsoft_id=user_data.get("microsoftId"),
            display_name=user_data.get("displayName"),
            photo_url=user_data.get("photoUrl"),
            created_at=user_data["createdAt"],
            last_login=user_data.get("lastLogin"),
        )

    async def update_user_role(self, user_id: str, role: UserRole) -> User:
        """
        Update user role

        Args:
            user_id: User ID
            role: New role

        Returns:
            Updated User object
        """
        user_ref = self.firestore_client.collection("users").document(user_id)
        await user_ref.update({"role": role.value})

        return await self.get_user(user_id)

    async def list_users(self) -> list[User]:
        """
        List all users

        Returns:
            List of User objects
        """
        users = []
        async for user_doc in self.firestore_client.collection("users").stream():
            user_data = user_doc.to_dict()
            users.append(
                User(
                    id=user_doc.id,
                    email=user_data["email"],
                    role=UserRole(user_data.get("role", "user")),
                    firebase_uid=user_data["firebaseUid"],
                    microsoft_id=user_data.get("microsoftId"),
                    display_name=user_data.get("displayName"),
                    photo_url=user_data.get("photoUrl"),
                    created_at=user_data["createdAt"],
                    last_login=user_data.get("lastLogin"),
                )
            )

        return users

    async def is_admin(self, user_id: str) -> bool:
        """
        Check if user is admin

        Args:
            user_id: User ID

        Returns:
            True if user is admin
        """
        user = await self.get_user(user_id)
        return user is not None and user.role == UserRole.ADMIN
