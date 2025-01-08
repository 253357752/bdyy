import requests
import base64
import pyaudio
import wave
import os
import threading
import tkinter as tk
from tkinter import messagebox

# 组装URL获取token，详见文档
base_url = "https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s"
APIKey = "mjW9Q5ttBUQairQYiqG5PQDp"
SecretKey = "rWNfuHrLrOGIGskbRsmFq2C1SwXsPNMA"

HOST = base_url % (APIKey, SecretKey)

def getToken(host):
    res = requests.get(host)
    return res.json()['access_token']

# 传入语音二进制数据，token
# dev_pid为百度语音识别提供的几种语言选择
def speech2text(speech_data, token, dev_pid=1537):
    FORMAT = 'wav'
    RATE = 16000
    CHANNEL = 1
    CUID = 'wate_play'
    SPEECH = base64.b64encode(speech_data).decode('utf-8')

    data = {
        'format': FORMAT,
        'rate': RATE,
        'channel': CHANNEL,
        'cuid': CUID,
        'len': len(speech_data),
        'speech': SPEECH,
        'token': token,
        'dev_pid': dev_pid
    }
    url = 'https://vop.baidu.com/server_api'
    headers = {'Content-Type': 'application/json'}
    print('正在识别...')
    r = requests.post(url, json=data, headers=headers)
    Result = r.json()
    if 'result' in Result:
        return Result['result'][0]
    else:
        error_code = Result.get('err_no', 'Unknown error code')
        error_message = Result.get('err_msg', 'Unknown error message')
        return f"Error: {error_code} - {error_message}"

def get_audio(filepath):
    CHUNK = 1024         # 定义数据流块
    FORMAT = pyaudio.paInt16  # 量化位数（音量级划分）
    CHANNELS = 1        # 声道数
    RATE = 16000         # 采样率
    RECORD_SECONDS = 5  # 录音秒数
    WAVE_OUTPUT_FILENAME = filepath  # wav文件路径
    p = pyaudio.PyAudio()  # 实例化

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print("*" * 10, "开始录音：请在5秒内输入语音")
    frames = []  # 定义一个列表
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):  # 循环，采样率16000 / 1024 * 5
        data = stream.read(CHUNK)  # 读取chunk个字节 保存到data中
        frames.append(data)  # 向列表frames中添加数据data
    print("*" * 10, "录音结束\n")

    stream.stop_stream()
    stream.close()  # 关闭
    p.terminate()  # 终结

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')  # 打开wav文件创建一个音频对象wf，开始写WAV文件
    wf.setnchannels(CHANNELS)  # 配置声道数
    wf.setsampwidth(p.get_sample_size(FORMAT))  # 配置量化位数
    wf.setframerate(RATE)  # 配置采样率
    wf.writeframes(b''.join(frames))  # 转换为二进制数据写入文件
    wf.close()  # 关闭
    return

def check_disk():
    import psutil
    list_drive = psutil.disk_partitions()  # 找出本地磁盘列表，保存的是结构体对象
    list_disk = []
    for drive in list_drive:
        list_disk.append(drive.device)
    return list_disk

def start_recognition():
    def run_recognition():
        try:
            get_audio(in_path)  # 录音

            with open(in_path, 'rb') as f:
                speech_data = f.read()

            res = speech2text(speech_data, token)  # 连接百度语音识别接口，得到识别结果
            text_box.insert(tk.END, f"识别结果：{res}\n")
        except Exception as e:
            text_box.insert(tk.END, f"发生错误：{str(e)}\n")

    threading.Thread(target=run_recognition).start()

if __name__ == '__main__':
    list_disk = check_disk()  # 检索本地磁盘
    dirname_path = os.path.join(list_disk[0], "voice")  # 设置语音文件存放路径

    if not os.path.exists(dirname_path):
        os.makedirs(dirname_path)

    filename = "voice.wav"  # 定义语音文件名
    in_path = os.path.join(dirname_path, filename)

    token = getToken(HOST)  # 获取Token

    # 创建主窗口
    root = tk.Tk()
    root.title("语音识别")
    root.geometry("400x300")

    # 创建文本框显示识别结果
    text_box = tk.Text(root, height=10, width=50)
    text_box.pack(pady=10)

    # 创建按钮开始录音和识别
    record_button = tk.Button(root, text="开始录音并识别", command=start_recognition)
    record_button.pack(pady=10)

    # 绑定 Enter 键到按钮的命令
    root.bind('<Return>', lambda event: record_button.invoke())

    # 运行主循环
    root.mainloop()