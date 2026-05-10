"""WebSocket 实时同步端点 - 客户端通过此接口接收实时变更"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 实时同步端点。
    客户端连接后，任何端的数据变更都会广播到此连接。
    保持简单：客户端不需要发送消息，只需接收服务器推送。
    """
    await ws_manager.connect(websocket)
    try:
        # 保持连接存活，客户端断开时自动清理
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
