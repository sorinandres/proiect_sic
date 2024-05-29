from flask import Flask, render_template, request
from app import PolarApp
from threading import Thread
import time

app = Flask(__name__)

p_app = PolarApp()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():

    request_data = request.get_json()
    device_name = request_data['deviceName']

    device_name = "Polar H10 " + device_name

    print(device_name)


    result = p_app.scan(device_name)
    if result == "Could not find device":
        return {"content": "Device not found"}
    elif result == "Could not scan for devices":
        return {"content": "Could not scan for devices"}
    else:
        return {"content": "Device found"}

@app.route('/connect')
def create_connection():
    res = p_app.connect()
    if res == False:
        return {"content": "Could not connect to device"}
    if p_app.is_connected():
        return {"content": "Device connected"}
    else:
        return {"content": "Could not connect to device"}

p_app_thread = Thread(target=p_app.run)

@app.route('/run')
def run():
    p_app_thread.start()

    while not p_app.running:
        time.sleep(0.1)
        continue

    return {"content": "Running"}

@app.route('/connect')
def connect():
    p_app.connect()
    return "Connecting..."

@app.route('/stop')
def stop():
    p_app.stop_ecg_stream()
    p_app.stop_acc_stream()
    p_app.signal_stop()
    p_app_thread.join()
    p_app.disconnect()
    return {"content": "Stopped"}

if __name__ == '__main__':
    app.run(debug=True)