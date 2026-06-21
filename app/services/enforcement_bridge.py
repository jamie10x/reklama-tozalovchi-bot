from __future__ import annotations

import asyncio
import contextlib
import json
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import BufferedInputFile, ChatPermissions
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.repositories.activity import ActivityRepository
from app.database.repositories.enforcement import EnforcementRepository
from app.database.secadmin_models import EnforcementAction
from app.database.session import get_secadmin_sessionmaker

logger = get_logger(__name__)

POLL_INTERVAL_SECONDS = 3
CLAIM_BATCH_SIZE = 5
WORKER_ID_PREFIX = "enforcement"


def _json_model(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json", exclude_none=True)
    return str(obj)


def _message_export_row(message) -> dict:
    return {
        "chat_id": message.chat_id,
        "message_id": message.message_id,
        "sender_id": message.sender_id,
        "sender_username": message.sender_username,
        "sender_first_name": message.sender_first_name,
        "sender_last_name": message.sender_last_name,
        "message_type": message.message_type,
        "text": message.text if message.text_stored else None,
        "text_stored": message.text_stored,
        "has_text": message.has_text,
        "is_edited": message.is_edited,
        "is_forwarded": message.is_forwarded,
        "reply_to_message_id": message.reply_to_message_id,
        "detection_status": message.detection_status,
        "risk_score": message.risk_score,
        "ad_score": message.ad_score,
        "security_score": message.security_score,
        "ai_score": message.ai_score,
        "detection_result": message.detection_result,
        "message_date": message.message_date.isoformat() if message.message_date else None,
        "created_at": message.created_at.isoformat() if message.created_at else None,
        "updated_at": message.updated_at.isoformat() if message.updated_at else None,
    }


class EnforcementBridge:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._running = False
        self._task: asyncio.Task | None = None
        self._worker_id = f"{WORKER_ID_PREFIX}-{id(self)}"

    async def _execute_action(self, action: EnforcementAction, session: AsyncSession) -> dict:
        action_type = action.action_type
        chat_id = action.target_chat_id
        message_id = action.target_message_id
        user_id = action.target_user_id

        if action_type == "delete_message":
            if chat_id is None or message_id is None:
                return {"error": "delete_message requires target_chat_id and target_message_id"}
            try:
                await self._bot.delete_message(chat_id=chat_id, message_id=message_id)
                return {"deleted": True}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "trust_sender":
            if user_id is None or chat_id is None:
                return {"error": "trust_sender requires target_user_id and target_chat_id"}
            try:
                await self._bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_audios=True,
                        can_send_documents=True,
                        can_send_photos=True,
                        can_send_videos=True,
                        can_send_video_notes=True,
                        can_send_voice_notes=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                    ),
                )
                return {"trusted": True}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "restrict_member":
            if user_id is None or chat_id is None:
                return {"error": "restrict_member requires target_user_id and target_chat_id"}
            try:
                await self._bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                    ),
                )
                return {"restricted": True}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "mute_member":
            if user_id is None or chat_id is None:
                return {"error": "mute_member requires target_user_id and target_chat_id"}
            try:
                until_date = int(datetime.now(timezone.utc).timestamp()) + 3600
                await self._bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until_date,
                )
                return {"muted": True, "until": until_date}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "ban_member":
            if user_id is None or chat_id is None:
                return {"error": "ban_member requires target_user_id and target_chat_id"}
            try:
                await self._bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                return {"banned": True}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "refresh_member":
            if user_id is None or chat_id is None:
                return {"error": "refresh_member requires target_user_id and target_chat_id"}
            try:
                member = await self._bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                return {"status": member.status, "user_id": user_id}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "refresh_group_permissions":
            if chat_id is None:
                return {"error": "refresh_group_permissions requires target_chat_id"}
            try:
                bot_member = await self._bot.get_chat_member(chat_id=chat_id, user_id=self._bot.id)
                can_delete = getattr(bot_member, "can_delete_messages", False)
                return {
                    "can_delete_messages": can_delete,
                    "status": bot_member.status,
                }
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "get_chat_info":
            if chat_id is None:
                return {"error": "get_chat_info requires target_chat_id"}
            try:
                chat = await self._bot.get_chat(chat_id=chat_id)
                return {"chat": _json_model(chat)}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "get_chat_administrators":
            if chat_id is None:
                return {"error": "get_chat_administrators requires target_chat_id"}
            try:
                admins = await self._bot.get_chat_administrators(chat_id=chat_id)
                return {"administrators": [_json_model(admin) for admin in admins]}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "get_chat_member_count":
            if chat_id is None:
                return {"error": "get_chat_member_count requires target_chat_id"}
            try:
                count = await self._bot.get_chat_member_count(chat_id=chat_id)
                return {"member_count": count}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "get_user_profile_photos":
            if user_id is None:
                return {"error": "get_user_profile_photos requires target_user_id"}
            try:
                photos = await self._bot.get_user_profile_photos(user_id=user_id, limit=5)
                return {"profile_photos": _json_model(photos)}
            except Exception as e:
                return {"error": str(e)}

        elif action_type == "save_observed_state":
            return {"saved": True, "info": "Observed state is continuously persisted"}

        elif action_type == "send_recent_messages":
            if chat_id is None:
                return {"error": "send_recent_messages requires target_chat_id"}
            if action.requested_by_officer_id is None:
                return {"error": "send_recent_messages requires requested_by_officer_id"}
            try:
                repo = ActivityRepository(session)
                messages = await repo.list_messages(limit=200, chat_id=chat_id)
                payload = {
                    "chat_id": chat_id,
                    "limit": 200,
                    "count": len(messages),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source": "observed_messages_database",
                    "telegram_history_note": (
                        "Telegram Bot API cannot fetch old chat history. This export contains only messages "
                        "the bot already observed and stored according to the capture policy."
                    ),
                    "messages": [_message_export_row(message) for message in messages],
                }
                content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                filename = f"observed-messages-{chat_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
                document = BufferedInputFile(content, filename=filename)
                await self._bot.send_document(
                    chat_id=action.requested_by_officer_id,
                    document=document,
                    caption=f"Last {len(messages)} observed messages for chat {chat_id}",
                )
                return {
                    "sent": True,
                    "recipient_id": action.requested_by_officer_id,
                    "chat_id": chat_id,
                    "message_count": len(messages),
                    "filename": filename,
                    "note": "Export includes only messages already observed and stored by this bot.",
                }
            except Exception as e:
                return {"error": str(e)}

        elif action_type in ("block_indicator", "allow_indicator"):
            return {"info": f"{action_type} logged but no Telegram API action needed"}

        return {"error": f"Unknown action_type: {action_type}"}

    async def _process_batch(self, session: AsyncSession) -> int:
        repo = EnforcementRepository(session)
        actions = await repo.claim_next(
            worker_id=self._worker_id,
            batch_size=CLAIM_BATCH_SIZE,
        )
        for action in actions:
            result = await self._execute_action(action, session)
            is_error = "error" in result
            if is_error:
                await repo.mark_failed(action.id, result=result)
                logger.warning(
                    "Enforcement failed",
                    action_id=str(action.id),
                    action_type=action.action_type,
                    chat_id=action.target_chat_id,
                    error=result["error"],
                )
            else:
                await repo.mark_completed(action.id, result=result)
                logger.info(
                    "Enforcement completed",
                    action_id=str(action.id),
                    action_type=action.action_type,
                    chat_id=action.target_chat_id,
                    result=result,
                )
            await session.flush()
        return len(actions)

    async def run_once(self) -> int:
        try:
            sm = get_secadmin_sessionmaker()
            async with sm() as session:
                processed = await self._process_batch(session)
                await session.commit()
                return processed
        except RuntimeError:
            return 0
        except Exception:
            logger.exception("EnforcementBridge run_once failed")
            return 0

    async def _loop(self) -> None:
        logger.info(
            "Enforcement bridge started",
            worker_id=self._worker_id,
        )
        while self._running:
            try:
                processed = await self.run_once()
                if processed > 0:
                    logger.info("Bridge processed %d enforcement actions", processed)
            except Exception:
                logger.exception("Bridge cycle error")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        logger.info("Enforcement bridge stopped")

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Enforcement bridge task created")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        logger.info("Enforcement bridge stopped")
