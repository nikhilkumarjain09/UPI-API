import cv2
import numpy as np
import socket
from flask import Flask, render_template, Response
import threading
import base64
import io
import struct
from PIL import Image
UDP_IP = '192.168.31.254'  # Server IP address
UDP_PORT = 12345  # Server port
BUFFER_SIZE = 102490
MYTTL = 1
# Dictionary to store video streams for each camera
video_streams = {}

# Create UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    
udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
ttl_bin = struct.pack('@i', MYTTL)
udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
udp_socket.bind((UDP_IP, UDP_PORT))

# Flask application
app = Flask(__name__)

@app.route('/<string:path>')
def index(path):
    return render_template('index.html',path=path)
@app.route('/video_feed/<camera_name>')
def video_feed(camera_name):
    def generate_frames():
        while True:
            #print(camera_name)
            if camera_name in video_streams:
                frame = video_streams[camera_name]
                #print(frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
def image_to_byte_array(image):
    byte_array = io.BytesIO()
    image.save(byte_array, format='PNG')
    byte_array.seek(0)
    return byte_array.read()

def receive_video_stream():
    while True:
        data, addr = udp_socket.recvfrom(BUFFER_SIZE)
        #print(data)
        data = data.decode('utf-8')
        #print(data)
        #print("HELLO")
        dataarr = data.split('$')
            #decodepath = dataarr[0]
        data = base64.b64decode(dataarr[1])
        path = base64.b64decode(dataarr[0])
        pathcheck = path.decode('utf-8')
        #print(pathcheck.replace("/",""))
        camera_name = pathcheck.replace("/","") # Use the sender's IP address as the camera name
        #print(camera_name)
        # Resize the frame to match the desired streaming resolution
        #frame = cv2.resize(frame, (640, 480))
        #frame.show()
        # Store the frame in the video stream dictionary
        np_data = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
        success, compressed_image = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 10])
            #print(path+"/"+listpath)
        data = compressed_image.tobytes()
                #print(type(data))
        #image = Image.open(io.BytesIO(data))
        #cropped_image = image.crop((0, 50, 430, 800))
        #new_image = cropped_image.resize((250, 600))
        #data = image_to_byte_array(cropped_image)
        video_streams[camera_name] = data
        #print(data)
        #print(video_streams[camera_name])

# Start a new thread to receive the video stream
thread = threading.Thread(target=receive_video_stream)
thread.start()

# Start the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4011)
