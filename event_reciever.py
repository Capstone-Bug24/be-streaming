from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import logging

app = Flask(__name__)
# 💡 핵심: SocketIO 설정을 추가합니다. cors_allowed_origins="*"는 프론트엔드 접속을 허용합니다.
socketio = SocketIO(app, cors_allowed_origins="*")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EventReceiver")

@app.route('/api/events', methods=['POST'])
def handle_ai_events():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400

    # 1. AI 데이터 분석 (Object Type, Confidence, BBox 등)
    obj_type = data.get('object_type', 'UNKNOWN')
    confidence = data.get('confidence', 0.0)
    bbox = data.get('bbox', {})

    # 2. 💡 웹소켓으로 프론트엔드에 즉시 전송 (Push)
    # 'ai_detection'이라는 이벤트 이름으로 데이터를 쏩니다.
    socketio.emit('ai_detection', {
        'label': obj_type,
        'confidence': f"{confidence:.2f}",
        'bbox': bbox
    })

    logger.info(f"📡 Forwarded to Frontend: {obj_type} ({confidence:.2f})")
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    # 💡 주의: app.run 대신 socketio.run을 사용해야 웹소켓이 작동합니다.
    logger.info("Starting WebSocket-enabled Event Receiver on port 5002...")
    socketio.run(app, host='0.0.0.0', port=5002)