import pyaudio
import wave
import requests
import json
import base64
import time
import sys

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
RECORD_SECONDS = 5        # seconds to record
WAVE_OUTPUT_FILENAME = "output.wav"

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

def record_audio():
    audio = pyaudio.PyAudio()

    try:
        # 打开音频流
        stream = audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

        print("开始录音...")

        frames = []

        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("录音结束")

        # 停止和关闭流
        stream.stop_stream()
        stream.close()

        # 保存录音文件
        with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

    finally:
        audio.terminate()

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

def main():
    try:
        # 获取访问令牌
        access_token = get_access_token(API_KEY, SECRET_KEY)

        # 录音
        record_audio()

        # 识别音频
        result = recognize_audio(access_token, WAVE_OUTPUT_FILENAME)
        print(f"识别结果: {result}")

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()