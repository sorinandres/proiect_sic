from flask import Flask, render_template, request, send_file
from app import PolarApp
from threading import Thread
import time
import zipfile

p_app = PolarApp()
time.sleep(1)
p_app._serial.blinkALLleds()

app = Flask(__name__)

p_app._serial.blinkALLleds()

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

p_app_thread = None

@app.route('/run')
def run():

    global p_app_thread

    p_app_thread = Thread(target=p_app.run)
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
    if p_app_thread is None:
        return {"content": "Not running"}
    p_app.stop_ecg_stream()
    p_app.stop_acc_stream()
    p_app.signal_stop = True
    p_app_thread.join()
    p_app.disconnect()
    return {"content": "Stopped"}

@app.route('/reset')
def reset():
    p_app.reset()
    return {"content": "Reset"}

@app.route('/download')
def download():

    ecgData = 'ecgData.txt'
    accData = 'accData.txt'

    zipf = zipfile.ZipFile('data.zip', 'w', zipfile.ZIP_DEFLATED)
    zipf.write(ecgData)
    zipf.write(accData)

    zipf.close()

    return send_file('data.zip')

if __name__ == '__main__':
    app.run(debug=True)