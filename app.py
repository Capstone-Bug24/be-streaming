import cv2
import time
import threading
from queue import Queue
from flask import Flask, Response

app = Flask(__name__)

# --- Configuration ---
# Maximum number of frames to buffer in memory to prevent data loss
BUFFER_SIZE = 30 
frame_queue = Queue(maxsize=BUFFER_SIZE)

def frame_producer():
    """
    Worker thread to capture frames from the camera and push them into the queue.
    This architecture ensures that camera capture remains independent of streaming speed.
    """
    # Use '0' for the built-in MacBook webcam. 
    # This will be replaced with an RTSP URL once the IoT device is ready.
    camera = cv2.VideoCapture(0) 
    
    while True:
        success, frame = camera.read()
        if not success:
            # Handle camera disconnection and attempt to reconnect
            print("LOG [Error]: Camera connection lost. Retrying in 5 seconds...")
            camera.release()
            time.sleep(5)
            camera = cv2.VideoCapture(0)
            continue

        # Data Loss Prevention: If the queue is full, drop the oldest frame to insert the newest one.
        # This keeps the stream as close to "real-time" as possible.
        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except:
                pass
        
        frame_queue.put(frame)

def generate_frames():
    """
    Consumer function with Smoothed FPS display to prevent flickering.
    """
    prev_time = time.time()
    frame_count = 0
    display_fps = 0 # This variable will hold the "readable" FPS value

    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            frame_count += 1

            # 1. Calculate the time difference for the current frame
            curr_time = time.time()
            time_diff = curr_time - prev_time
            
            # 2. Update the readable FPS only once every 30 frames
            # This prevents the numbers from changing too fast to read
            if frame_count % 30 == 0:
                if time_diff > 0:
                    # Calculate average FPS over the last 30 frames
                    # Formula: Total Frames / Total Time Elapsed
                    display_fps = int(30 / time_diff)
                
                # Update prev_time and reset frame_count for the next second
                prev_time = curr_time
                print(f"LOG [Performance]: Smoothed FPS: {display_fps}")

            # 3. Draw the STABLE FPS number on the frame
            # Using the 'display_fps' variable which only changes once a second
            cv2.putText(frame, f"FPS: {display_fps}", (10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # 4. Stream the frame
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
    """
    Endpoint for the frontend to access the live stream.
    """
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    # Initialize and start the background thread for camera capture (Producer)
    producer_thread = threading.Thread(target=frame_producer, daemon=True)
    producer_thread.start()
    
    # Run the Flask development server on port 5001
    app.run(host='0.0.0.0', port=5001, threaded=True)