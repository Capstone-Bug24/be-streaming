import cv2
import time
import threading
from datetime import datetime
from queue import Queue
from flask import Flask, Response

app = Flask(__name__)

# --- Configuration ---
BUFFER_SIZE = 30 
frame_queue = Queue(maxsize=BUFFER_SIZE)

# 하드코딩 방지. URL을 상단 변수로 빼서 관리
CAMERA_SOURCE = "rtsp://100.68.95.52:8554/mystream" # 카메라 주소
# CAMERA_SOURCE = 0 # 테스트용 내장 카메라가 필요할 땐 이 줄의 주석을 풀고 위를 주석 처리

def frame_producer():
    """Worker thread to capture frames using Producer-Consumer pattern."""
    
    camera = cv2.VideoCapture(CAMERA_SOURCE)
    
    while True:
        success, frame = camera.read()
        if not success:
            print(f"LOG [Error]: Camera connection lost to {CAMERA_SOURCE}. Retrying in 5 seconds...")
            camera.release()
            time.sleep(5)
            # 🚨 크리티컬 수정: 재연결 시에도 0이 아닌 CAMERA_SOURCE를 사용해야 합니다.
            camera = cv2.VideoCapture(CAMERA_SOURCE)
            continue

        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except:
                pass
        
        frame_queue.put(frame)

def generate_frames():
    """Consumer function with FPS and Timestamp overlay."""
    prev_time = time.time()
    frame_count = 0
    display_fps = 0 

    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            frame_count += 1

            curr_time = time.time()
            time_diff = curr_time - prev_time
            
            if frame_count % 30 == 0:
                if time_diff > 0:
                    display_fps = int(30 / time_diff)
                
                prev_time = curr_time
                print(f"LOG [Performance]: Smoothed FPS: {display_fps}")

            # 💡 기존 기능: FPS 그리기 (좌측 상단)
            cv2.putText(frame, f"FPS: {display_fps}", (10, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # 💡 추가 기능: 타임스탬프 그리기 (우측 상단)
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, current_time_str, (frame.shape[1] - 300, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Stream the frame
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(0.01)
                        
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    producer_thread = threading.Thread(target=frame_producer, daemon=True)
    producer_thread.start()
    
    app.run(host='0.0.0.0', port=5001, threaded=True)