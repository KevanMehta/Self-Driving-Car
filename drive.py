# initially car is steady with throttle and steering 0 then simulator send image of track to model and model will extract the feature from image and predict steering angle which we send back to simulator

import socketio
import eventlet
from flask import Flask                  # microframework to  build webapps
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import cv2

# realtime communication btn client and server (bidirectional communication with simulator)
sio = socketio.Server()
app = Flask(__name__)  # '__main__'
speed_limit = 10


def img_preprocess(img):
    img = img[60:135, :, :]                           # y-axis(60-135)
    # convert rgb to yuv format because for nvidia neural model this color space is efficient
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    # smoothing the image and reduce noise ((3,3) kernel size,deviation = 0)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img / 255
    return img

# listening updates that will send to telemetry from simulator


@sio.on('telemetry')
def telemetry(sid, data):
    # decode base64 image and to mimic our data like normal file
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    image = np.asarray(image)
    image = img_preprocess(image)
    image = np.array([image])
    speed = float(data['speed'])
    throttle = 1.0 - speed / speed_limit
    steering_angle = float(model.predict(image))
    print('{} {} {}'.format(steering_angle, throttle, speed))
    send_control(steering_angle, throttle)

# connection with client


@sio.on('connect')
def connect(sid, environ):        # sessionId of client and environment
    print('Connected')
    send_control(0, 0)


def send_control(steering_angle, throttle):
    sio.emit('steer', data={
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })


if __name__ == '__main__':
    model = load_model('model5.h5')   # load_model
    # connect socketio with flask
    app = socketio.Middleware(sio, app)
    # web server gateway interface(wsgi) listen on any available ip on port 4567 and request send to app
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)
