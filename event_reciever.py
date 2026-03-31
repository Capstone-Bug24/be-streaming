from flask import Flask, request, jsonify
import logging
import json

app = Flask(__name__)

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EventReceiver")

@app.route('/api/events', methods=['POST'])
def handle_ai_events():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400

    # 1. Extract Key Info
    obj = data.get('object_type', 'UNKNOWN')
    conf = data.get('confidence', 0)
    cam = data.get('camera_id', 'N/A')
    
    # 2. Extract BBox for logic (using LaTeX for clarity in documentation)
    # The box is defined by $[x_1, y_1, x_2, y_2]$
    bbox = data.get('bbox', {})
    width = bbox.get('x2', 0) - bbox.get('x1', 0)

    # 3. SUMMARY LOG (Clean & Readable)
    # Professional developers use one-line summaries for high-traffic logs
    logger.info(f"🟢 [DETECTION] Cam: {cam} | Obj: {obj} | Conf: {conf:.2f} | Width: {width}px")

    # 4. DEBUG LOG (Hidden unless needed)
    # Only use 'print(json.dumps...)' if you are actively fixing a bug
    # logger.debug(json.dumps(data, indent=2)) 

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    logger.info("Starting Event Receiver on port 5002...")
    app.run(host='0.0.0.0', port=5002)