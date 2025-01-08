import pyaudio
import wave
import requests
import json
import base64
import time
import sys
import tkinter as tk
from tkinter import messagebox

# 设置默认编码为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 百度语音识别相关参数
API_KEY = 'mjW9Q5ttBUQairQYiqG5PQDp'
SECRET_KEY = 'rWNfuHrLrOGIGskbRsmFq2C1SwXsPNMA'
TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
ASR_URL = 'https://vop.baidu.com/server_api'

# 录音参数
FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNELS = 1              # 1 channel
RATE = 16000              # 16kHz sampling rate
CHUNK = 1024              # 2^10 samples for buffer
WAVE_OUTPUT_FILENAME = "output.wav"

class AudioRecorder:
    def __init__(self, root):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False
        self.root = root  # 传递 root 对象

    def start_recording(self):
        self.recording = True
        self.frames = []
        self.stream = self.audio.open(format=FORMAT,
                                     channels=CHANNELS,
                                     rate=RATE,
                                     input=True,
                                     frames_per_buffer=CHUNK)
        print("开始录音...")
        self.record()

    def record(self):
        if self.recording:
            data = self.stream.read(CHUNK)
            self.frames.append(data)
            self.root.after(10, self.record)  # 每 10 毫秒读取一次数据

    def stop_recording(self):
        self.recording = False
        print("录音结束")
        self.stream.stop_stream()
        self.stream.close()
        with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.frames))
        self.audio.terminate()

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

def recognize_audio(access_token, audio_file_path):
    with open(audio_file_path, 'rb') as audio_file:
        audio_data = audio_file.read()

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
        recorder.stop_recording()
        stop_button.config(state=tk.DISABLED)
        start_button.config(state=tk.NORMAL)
        try:
            # 获取访问令牌
            access_token = get_access_token(API_KEY, SECRET_KEY)

            # 识别音频
            result = recognize_audio(access_token, WAVE_OUTPUT_FILENAME)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"识别结果: {result}")

        except Exception as e:
            messagebox.showerror("发生错误", f"发生错误: {e}")

def main():
    global recorder, root, start_button, stop_button, result_text

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

    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()