"""WebSocket endpoint for real-time scan progress via Redis pub/sub."""
import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# How long (seconds) to wait for a new message before sending a keepalive ping
_KEEPALIVE_INTERVAL = 25


@router.websocket("/ws/scans/{scan_id}/progress")
async def scan_progress_ws(websocket: WebSocket, scan_id: str) -> None:
    """Stream real-time scan progress updates over WebSocket.

    The Celery orchestrator publishes JSON progress updates to the Redis
    channel ``scan:{scan_id}:progress`` every time the scan status or
    progress percentage changes.  This endpoint subscribes to that channel
    and forwards each message to the connected browser client.

    Protocol:
        Server → Client messages (JSON):
          {"type": "progress", "scan_id": "...", "status": "scanning",
           "progress": 45, "pages_found": 20, "pages_scanned": 9}
          {"type": "done"}      — sent when status is 'completed' or 'failed'
          {"type": "ping"}      — keepalive every ~25 s of inactivity

        Client → Server:
          Any message is treated as a ping-reply (client keeps the connection alive).
          Send "close" to request graceful disconnection.
    """
    await websocket.accept()
    channel = f"scan:{scan_id}:progress"
    logger.info(f"WebSocket connected for scan {scan_id}")

    try:
        import redis.asyncio as aioredis
    except ImportError:
        # Graceful degradation: tell client to fall back to polling
        await websocket.send_text(json.dumps({"type": "error", "message": "redis not available, use polling"}))
        await websocket.close()
        return

    try:
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
            pubsub = r.pubsub()
            await pubsub.subscribe(channel)

            try:
                while True:
                    # Wait for message with a timeout for keepalive
                    try:
                        message = await asyncio.wait_for(
                            pubsub.get_message(ignore_subscribe_messages=True),
                            timeout=_KEEPALIVE_INTERVAL,
                        )
                    except asyncio.TimeoutError:
                        # Send keepalive ping so the connection stays open
                        try:
                            await websocket.send_text(json.dumps({"type": "ping"}))
                        except Exception:
                            break
                        continue

                    if message is None:
                        # No message yet — yield control and retry
                        await asyncio.sleep(0.1)
                        continue

                    if message["type"] == "message":
                        raw = message["data"]
                        try:
                            await websocket.send_text(raw)
                        except Exception:
                            break

                        # Close connection when scan reaches a terminal state
                        try:
                            data = json.loads(raw)
                            if data.get("status") in ("completed", "failed", "cancelled"):
                                await websocket.send_text(json.dumps({"type": "done"}))
                                break
                        except (json.JSONDecodeError, TypeError):
                            pass

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for scan {scan_id}")
            finally:
                await pubsub.unsubscribe(channel)
                await pubsub.close()

    except Exception as e:
        logger.error(f"WebSocket error for scan {scan_id}: {e}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"WebSocket closed for scan {scan_id}")
