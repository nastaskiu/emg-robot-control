import serial
import time
import joblib
import numpy as np

from flask import Flask, render_template
from flask_socketio import SocketIO

PORT = 'COM3'
BAUD = 115200

model = joblib.load('emg_model.pkl')

ser = serial.Serial(PORT, BAUD)
time.sleep(2)

START_THRESHOLD = 1
SILENCE_SAMPLES = 12
MIN_GESTURE_SAMPLES = 8

STOP_TIMEOUT = 1.2

CONF_THRESHOLD = 0.65  # порог уверенности

# пороги по длительности для жеста вперед
SHORT_MAX = 2.0      # s  -> FORWARD
MEDIUM_MAX = 2.4     # s  -> LEFT
LONG_MIN = 2.6       # s  -> BACKWARD

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


def extract_features(env_window, out_window):
    env = np.array(env_window)
    out = np.array(out_window)
    return np.array([[
        np.mean(env),
        np.std(env),
        np.max(env),
        np.min(env),
        np.sqrt(np.mean(env ** 2)),
        np.sum(np.abs(env)),

        np.mean(out),
        np.std(out),
        np.max(out),
        np.sum(out),
        np.count_nonzero(out),
    ]])


def classify_gesture(env_segment, out_segment):
    features = extract_features(env_segment, out_segment)
    label = model.predict(features)[0]

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(features)[0]
        confidence = float(np.max(proba))
    else:
        confidence = 1.0

    return label, confidence


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    print('Client connected')


def emg_loop():
    print("LIVE EMG STARTED")
    gesture_active = False
    env_segment = []
    out_segment = []
    silence_count = 0

    last_command_time = time.time()
    stop_sent = False

    while True:
        line = ser.readline().decode(errors='ignore').strip()
        try:
            envelope_str, output_str = line.split(',')
            envelope = float(envelope_str)
            output = float(output_str)
        except:
            continue

        # сырые значения для графика
        socketio.emit('emg_sample', {
            'envelope': envelope,
            'output': output,
            'time': time.time()
        })

        if not gesture_active and output > START_THRESHOLD:
            gesture_active = True
            env_segment = []
            out_segment = []
            silence_count = 0

        if gesture_active:
            env_segment.append(envelope)
            out_segment.append(output)

        if output <= START_THRESHOLD:
            silence_count += 1
        else:
            silence_count = 0

        if silence_count >= SILENCE_SAMPLES:
            if len(out_segment) >= MIN_GESTURE_SAMPLES and max(out_segment) > 0:
                label, confidence = classify_gesture(env_segment, out_segment)
                gesture_duration = len(out_segment) * 0.02

                if confidence < CONF_THRESHOLD:
                    msg = (f"UNKNOWN ({label}, conf={confidence:.2f}, "
                           f"dur={gesture_duration:.2f}s)")
                    cmd = 'STOP'
                    gesture_type = 'UNKNOWN'
                else:
                    # новая логика команд
                    if label == 'wrist_back2':
                        cmd = 'RIGHT'
                        gesture_type = 'BACK_ANY'
                    elif label == 'wrist_forward2':
                        if gesture_duration <= SHORT_MAX:
                            cmd = 'FORWARD'
                            gesture_type = 'FORWARD_SHORT'
                        elif gesture_duration <= MEDIUM_MAX:
                            cmd = 'LEFT'
                            gesture_type = 'FORWARD_MEDIUM'
                        elif gesture_duration >= LONG_MIN:
                            cmd = 'BACKWARD'
                            gesture_type = 'FORWARD_LONG'
                        else:
                            cmd = 'STOP'
                            gesture_type = 'FORWARD_AMBIG'
                    else:
                        cmd = 'STOP'
                        gesture_type = 'UNKNOWN_LABEL'

                    msg = (f"{gesture_type} {label} -> {cmd} "
                           f"duration={gesture_duration:.2f}s "
                           f"conf={confidence:.2f}")

                print(msg)

                socketio.emit('command', {
                    'message': msg,
                    'command': cmd,
                    'type': gesture_type,
                    'label': label,
                    'confidence': confidence,
                    'duration': gesture_duration
                })

                last_command_time = time.time()
                stop_sent = False

            gesture_active = False
            env_segment = []
            out_segment = []
            silence_count = 0

        if not gesture_active and time.time() - last_command_time > STOP_TIMEOUT and not stop_sent:
            msg = "rest -> STOP"
            print(msg)
            socketio.emit('command', {
                'message': msg,
                'command': 'STOP',
                'type': 'REST',
                'label': 'rest',
                'confidence': 1.0,
                'duration': 0.0
            })
            stop_sent = True

        socketio.sleep(0.01)


@socketio.on('start_emg')
def start_emg(message):
    socketio.start_background_task(emg_loop)


if __name__ == '__main__':
    socketio.run(
        app,
        host='127.0.0.1',
        port=5000,
        allow_unsafe_werkzeug=True
    )