"""
Database chat operations for StoryOS v2
Handles CRUD operations for chat messages and visual prompts in MongoDB
"""

import time
from backend.utils.streamlit_shim import st
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo.database import Database
from backend.logging_config import get_logger, StoryOSLogger

# Model imports
from backend.models.message import Message
from backend.models.image_prompts import VisualPrompts


class DbChatActions:
    """Handles chat-related database operations"""

    def __init__(self, db: Database):
        """Initialize with database connection"""
        self.db = db
        self.logger = get_logger("database.chat_actions")
        self.logger.debug("DbChatActions initialized")

    @staticmethod
    def find_message(messages: List[Message], message_id: str) -> Optional[Message]:
        """Find a message by its message_id field from a list of Message objects"""
        for msg in messages:
            if msg.message_id == message_id:
                return msg
        return None

    def create_chat_document(self, game_session_id: str) -> bool:
        """Create a new chat document for a game session"""
        start_time = time.time()
        self.logger.info(f"Creating chat document for game session: {game_session_id}")
        
        try:
            if self.db is None:
                self.logger.error("Cannot create chat document - database not connected")
                return False
                
            from bson import ObjectId
            chat_doc = {
                'game_session_id': ObjectId(game_session_id),
                'messages': [],
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.db.chats.insert_one(chat_doc)
            success = result.inserted_id is not None
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"Chat document created successfully: {result.inserted_id} for session: {game_session_id}")
                StoryOSLogger.log_performance("database", "create_chat_document", duration, {
                    "game_session_id": game_session_id,
                    "chat_document_id": str(result.inserted_id)
                })
            else:
                self.logger.error(f"Chat document creation failed - no document ID returned for session: {game_session_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating chat document for session {game_session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "create_chat_document", "game_session_id": game_session_id})
            st.error(f"Error creating chat document: {str(e)}")
            return False

    def add_chat_message(
        self,
        game_session_id: str,
        sender: str,
        content: str,
        full_prompt: Optional[List[Dict[str, Any]]] = None,
        *,
        role: Optional[str] = None,
    ) -> bool:
        """Add a message to the chat"""
        start_time = time.time()
        content_length = len(content)
        self.logger.debug(f"Adding chat message from {sender} to session {game_session_id} (length: {content_length})")

        try:
            if self.db is None:
                self.logger.error("Cannot add chat message - database not connected")
                return False
                
            from bson import ObjectId
            chat_filter = {'game_session_id': ObjectId(game_session_id)}
            chat_doc = self.db.chats.find_one(chat_filter, {'messages': 1})
            message_idx = len(chat_doc.get('messages', [])) if chat_doc and isinstance(chat_doc.get('messages'), list) else 0

            message = Message.create_chat_message(
                sender=sender,
                content=content,
                message_id=f"{game_session_id}_{message_idx}",
                role=role,
                full_prompt=full_prompt,
            )

            message_record = {
                key: value
                for key, value in message.to_dict().items()
                if value is not None
            }

            # Ensure timestamps are always stored
            if not message_record.get('timestamp'):
                message_record['timestamp'] = datetime.utcnow().isoformat()

            result = self.db.chats.update_one(
                chat_filter,
                {'$push': {'messages': message_record}}
            )
            
            success = result.modified_count > 0
            duration = time.time() - start_time
            
            if success:
                self.logger.debug(f"Chat message added successfully from {sender} to session {game_session_id}")
                StoryOSLogger.log_performance("database", "add_chat_message", duration, {
                    "game_session_id": game_session_id,
                    "sender": sender,
                    "content_length": content_length,
                    "modified_count": result.modified_count
                })
            else:
                self.logger.warning(f"Chat message add resulted in 0 modifications for session {game_session_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding chat message from {sender} to session {game_session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {
                "operation": "add_chat_message", 
                "game_session_id": game_session_id, 
                "sender": sender,
                "content_length": content_length
            })
            st.error(f"Error adding chat message: {str(e)}")
            return False

    def get_chat_messages(self, game_session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get chat messages for a game session"""
        start_time = time.time()
        self.logger.debug(f"Retrieving chat messages for session: {game_session_id} (limit: {limit})")

        try:
            if self.db is None:
                self.logger.error("Cannot get chat messages - database not connected")
                return []
                
            from bson import ObjectId
            chat_doc = self.db.chats.find_one({'game_session_id': ObjectId(game_session_id)})

            if not chat_doc or 'messages' not in chat_doc:
                self.logger.debug(f"No chat document or messages found for session: {game_session_id}")
                return []
                
            messages_payload = chat_doc.get('messages', [])
            if not isinstance(messages_payload, list):
                self.logger.error("Messages payload malformed for session: %s", game_session_id)
                return []

            original_count = len(messages_payload)

            if limit and len(messages_payload) > limit:
                messages_payload = messages_payload[-limit:]

            messages: List[Message] = []
            for raw_message in messages_payload:
                if isinstance(raw_message, Message):
                    # Convert escaped newlines to actual newlines
                    if raw_message.content:
                        raw_message.content = raw_message.content.replace('\\n', '\n')
                    messages.append(raw_message)
                    continue

                if isinstance(raw_message, dict):
                    # Convert escaped newlines to actual newlines in content
                    if 'content' in raw_message and raw_message['content']:
                        raw_message['content'] = raw_message['content'].replace('\\n', '\n')

                    message = Message.from_dict(raw_message)
                    if message.timestamp is None:
                        message.timestamp = datetime.utcnow().isoformat()
                    messages.append(message)
                else:
                    self.logger.warning(
                        "Encountered unexpected message payload type %s for session %s",
                        type(raw_message),
                        game_session_id,
                    )

            duration = time.time() - start_time
            self.logger.debug(f"Retrieved {len(messages)}/{original_count} chat messages for session: {game_session_id}")
            StoryOSLogger.log_performance("database", "get_chat_messages", duration, {
                "game_session_id": game_session_id,
                "total_messages": original_count,
                "returned_messages": len(messages),
                "limit": limit
            })
                
            return messages
                
        except Exception as e:
            self.logger.error(f"Error getting chat messages for session {game_session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {"operation": "get_chat_messages", "game_session_id": game_session_id})
            st.error(f"Error getting chat messages: {str(e)}")
            return []
        
    def add_image_url_to_visual_prompt(
        self,
        session_id: str,
        message_id: str,
        prompt: str,
        image_url: str,
    ) -> bool:
        """Add an image URL to a specific visual prompt in a chat message."""
        start_time = time.time()
        self.logger.debug(f"Adding image URL to visual prompt for session {session_id}, message {message_id}")

        try:
            if self.db is None:
                self.logger.error("Cannot update visual prompt - database not connected")
                return False

            from bson import ObjectId

            chat_doc = self.db.chats.find_one({'game_session_id': ObjectId(session_id)})
            if not chat_doc or 'messages' not in chat_doc:
                self.logger.warning(f"No chat document found for session: {session_id}")
                return False

            raw_messages = chat_doc.get('messages', [])
            if not isinstance(raw_messages, list):
                self.logger.error("Message payload malformed for session: %s", session_id)
                return False
            
            # Convert raw messages to Message objects
            messages: List[Message] = []
            for raw_message in raw_messages:
                if isinstance(raw_message, Message):
                    messages.append(raw_message)
                elif isinstance(raw_message, dict):
                    message = Message.from_dict(raw_message)
                    if message.timestamp is None:
                        message.timestamp = datetime.utcnow().isoformat()
                    messages.append(message)
                else:
                    self.logger.warning(
                        "Encountered unexpected message payload type %s for session %s",
                        type(raw_message),
                        session_id,
                    )
            
            # Find the message with the matching message_id field
            message = self.find_message(messages, str(message_id))
            
            if message is None:
                self.logger.warning(
                    "No message found with message_id %s in session %s (total messages=%s)",
                    message_id,
                    session_id,
                    len(messages),
                )
                return False
            
            if not message.visual_prompts or not isinstance(message.visual_prompts, dict):
                message.visual_prompts = {}

            # Update or add the image URL for the given prompt
            message.visual_prompts[prompt] = image_url
            if message.timestamp is None:
                message.timestamp = datetime.utcnow().isoformat()

            # Convert messages to JSON/dict format for MongoDB storage
            serialized_messages = [
                {key: value for key, value in msg.to_dict().items() if value is not None}
                for msg in messages
            ]

            # Store messages as dictionaries that MongoDB can handle
            result = self.db.chats.update_one(
                {'_id': chat_doc['_id']},
                {'$set': {'messages': serialized_messages}}
            )

            duration = time.time() - start_time
            StoryOSLogger.log_performance("database", "add_image_url_to_visual_prompt", duration, {
                "session_id": session_id,
                "message_id": message_id,
                "prompt": prompt
            })

            return result.modified_count > 0
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error adding image URL to visual prompt for session {session_id}, message {message_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {
                "operation": "add_image_url_to_visual_prompt",
                "session_id": session_id,
                "message_id": message_id,
                "prompt": prompt,
                "duration": duration,
            })
            return False

    def add_visual_prompts_to_latest_message(self, session_id: str, prompts: VisualPrompts) -> bool:
        """Attach visualization prompts to the latest chat message for a session."""
        start_time = time.time()
        self.logger.debug(f"Adding visual prompts to latest message for session: {session_id}")

        try:
            if self.db is None:
                self.logger.error("Cannot update chat message - database not connected")
                return False

            from bson import ObjectId

            chat_doc = self.db.chats.find_one({'game_session_id': ObjectId(session_id)})
            if not chat_doc or 'messages' not in chat_doc:
                self.logger.warning(f"No chat document found for session: {session_id}")
                return False

            raw_messages = chat_doc.get('messages', [])
            if not isinstance(raw_messages, list):
                self.logger.error("Message payload malformed for session: %s", session_id)
                return False

            if not raw_messages:
                self.logger.warning(f"Chat document has no messages for session: {session_id}")
                return False

            visual_prompts_payload = {
                prompts.visual_prompt_1: "",
                prompts.visual_prompt_2: "",
                prompts.visual_prompt_3: ""
            }

            messages: List[Message] = []
            for raw_message in raw_messages:
                if isinstance(raw_message, Message):
                    messages.append(raw_message)
                elif isinstance(raw_message, dict):
                    messages.append(Message.from_dict(raw_message))
                else:
                    self.logger.warning(
                        "Unexpected message type %s in session %s",
                        type(raw_message),
                        session_id,
                    )
                    continue

            if not messages:
                self.logger.warning("No parsable messages found for session: %s", session_id)
                return False

            # Find the latest message from dungeon_master/StoryOS, not just the latest message
            latest_dm_message = None
            for message in reversed(messages):
                if message.sender in ['dungeon_master', 'StoryOS', 'story']:
                    latest_dm_message = message
                    break

            if not latest_dm_message:
                self.logger.warning("No dungeon master message found for session: %s", session_id)
                return False

            latest_dm_message.visual_prompts = visual_prompts_payload
            if latest_dm_message.timestamp is None:
                latest_dm_message.timestamp = datetime.utcnow().isoformat()

            # Convert messages to JSON/dict format for MongoDB storage
            serialized_messages = [
                {key: value for key, value in msg.to_dict().items() if value is not None}
                for msg in messages
            ]

            # Store messages as dictionaries that MongoDB can handle
            result = self.db.chats.update_one(
                {'_id': chat_doc['_id']},
                {'$set': {'messages': serialized_messages}}
            )

            duration = time.time() - start_time
            StoryOSLogger.log_performance("database", "add_visual_prompts_to_latest_message", duration, {
                "session_id": session_id,
                "modified_count": result.modified_count,
            })

            success = result.modified_count > 0
            if success:
                self.logger.debug(f"Visual prompts appended to latest message for session: {session_id}")
            else:
                self.logger.warning(f"No messages updated when attaching visual prompts for session: {session_id}")

            return success

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error attaching visual prompts for session {session_id}: {str(e)}")
            StoryOSLogger.log_error_with_context("database", e, {
                "operation": "add_visual_prompts_to_latest_message",
                "session_id": session_id,
                "duration": duration,
            })
            return False

    def get_visual_prompts(self, session_id: str, message_id: int) -> Dict[str, str]:
        """Return the visual prompts for a specific message in a chat session."""
        start_time = time.time()
        self.logger.debug(
            "Fetching visual prompts for session %s at index %s",
            session_id,
            message_id,
        )

        try:
            if self.db is None:
                self.logger.error("Cannot fetch visual prompts - database not connected")
                return {}

            from bson import ObjectId

            chat_doc = self.db.chats.find_one({'game_session_id': ObjectId(session_id)})
            if not chat_doc:
                self.logger.warning("No chat document found for session: %s", session_id)
                return {}

            messages_payload = chat_doc.get('messages', [])
            if not isinstance(messages_payload, list):
                self.logger.error("Messages payload malformed for session: %s", session_id)
                return {}

            if message_id < 0 or message_id >= len(messages_payload):
                self.logger.warning(
                    "Chat index %s out of range for session %s (messages=%s)",
                    message_id,
                    session_id,
                    len(messages_payload),
                )
                return {}

            raw_message = messages_payload[message_id]
            if isinstance(raw_message, Message):
                message = raw_message
            elif isinstance(raw_message, dict):
                message = Message.from_dict(raw_message)
            else:
                self.logger.error(
                    "Message at index %s is unexpected type %s for session %s",
                    message_id,
                    type(raw_message),
                    session_id,
                )
                return {}

            prompts = message.visual_prompts
            if not isinstance(prompts, list) or len(prompts) < 3:
                self.logger.warning(
                    "Visual prompts missing or incomplete for session %s message %s",
                    session_id,
                    message_id,
                )
                return {}

            duration = time.time() - start_time
            StoryOSLogger.log_performance("database", "get_visual_prompts", duration, {
                "session_id": session_id,
                "chat_idx": message_id,
                "returned_prompts": len(prompts),
            })

            return prompts

        except Exception as exc:
            duration = time.time() - start_time
            self.logger.error(
                "Error retrieving visual prompts for session %s message %s: %s",
                session_id,
                message_id,
                str(exc),
            )
            StoryOSLogger.log_error_with_context("database", exc, {
                "operation": "get_visual_prompts",
                "session_id": session_id,
                "chat_idx": message_id,
                "duration": duration,
            })
            return {}
