"""WebSocket 连接管理器 - 实现多端实时同步"""
from typing import Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class WSConnectionManager:
    """
    WebSocket 连接管理器。
    维护所有活跃的 WebSocket 连接，当一个端产生数据变更时，
    广播给所有其他端，实现实时同步。
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"新客户端连接，当前在线: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"客户端断开，当前在线: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, payload: dict, exclude: WebSocket = None):
        """
        广播消息给所有（或指定排除之外的）客户端。
        event_type: sync_task / sync_travel_plan / sync_note / delete_*
        """
        message = json.dumps({"type": event_type, "data": payload}, ensure_ascii=False)
        dead = set()
        for conn in self.active_connections:
            if conn is exclude:
                continue
            try:
                await conn.send_text(message)
            except Exception:
                dead.add(conn)
        for d in dead:
            self.active_connections.discard(d)


ws_manager = WSConnectionManager()
