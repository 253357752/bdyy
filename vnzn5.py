import sounddevice as sd
import soundfile as sf
import requests
import json
import base64
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# 百度语音识别相关参数
API_KEY = 'mjW9Q5ttBUQairQYiqG5PQDp'
SECRET_KEY = 'rWNfuHrLrOGIGskbRsmFq2C1SwXsPNMA'
TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
ASR_URL = 'https://vop.baidu.com/server_api'

# 录音参数
FORMAT = 'int16'  # 16-bit resolution
CHANNELS = 1       # 1 channel
RATE = 16000       # 16kHz sampling rate
RECORD_SECONDS = 5 # seconds to record

class AudioRecorder:
    def __init__(self, root):
        self.recording = False
        self.frames = []
        self.root = root  # 传递 root 对象
        self.stream = None

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.frames = []
            print("开始录音...")
            self.stream = sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16', callback=self.record_callback)
            self.stream.start()

    def record_callback(self, indata, frames, time, status):
        if self.recording:
            self.frames.append(indata.copy())

    def stop_recording(self):
        if self.recording:
            self.recording = False
            print("录音结束")
            self.stream.stop()
            self.stream.close()
            # 将 frames 列表中的所有数组合并成一个完整的数组
            audio_data = np.concatenate(self.frames, axis=0)
            return audio_data

def get_access_token(api_key, secret_key):
    params = {
        'grant_type': 'client_credentials',
        'client_id': api_key,
        'client_secret': secret_key
    }
    response = requests.get(TOKEN_URL, params=params)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Failed to get access token: {response.text}")

def recognize_audio(access_token, audio_data):
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        'format': 'wav',
        'rate': RATE,
        'channel': CHANNELS,
        'cuid': 'your_cuid',  # 请替换为实际的 CUID
        'token': access_token,
        'speech': audio_base64,
        'len': len(audio_data)
    }

    response = requests.post(ASR_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            return result['result'][0]
        else:
            return "无法识别语音"
    else:
        return f"请求失败: {response.text}"

def start_recording():
    if not recorder.recording:
        recorder.start_recording()
        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)

def stop_recording():
    if recorder.recording:
        audio_data = recorder.stop_recording()
        stop_button.config(state=tk.DISABLED)
        start_button.config(state=tk.NORMAL)
        # 使用线程池来执行识别任务
        executor.submit(recognize_audio_thread, audio_data)

def recognize_audio_thread(audio_data):
    try:
        # 使用预先获取的访问令牌
        result = recognize_audio(access_token, audio_data)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"识别结果: {result}")

    except Exception as e:
        messagebox.showerror("发生错误", f"发生错误: {e}")

def main():
    global recorder, root, start_button, stop_button, result_text, access_token

    # 预先获取访问令牌
    access_token = get_access_token(API_KEY, SECRET_KEY)

    # 创建主窗口
    root = tk.Tk()
    root.title("语音识别")

    # 创建开始录音按钮
    start_button = tk.Button(root, text="开始录音", command=start_recording)
    start_button.pack(pady=10)

    # 创建停止录音按钮
    stop_button = tk.Button(root, text="停止录音并识别", command=stop_recording, state=tk.DISABLED)
    stop_button.pack(pady=10)

    # 创建文本框显示识别结果
    result_text = tk.Text(root, height=10, width=50)
    result_text.pack(pady=20)

    # 初始化录音器，传递 root 对象
    recorder = AudioRecorder(root)

    # 创建一个线程池
    global executor
    executor = ThreadPoolExecutor(max_workers=5)

    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()