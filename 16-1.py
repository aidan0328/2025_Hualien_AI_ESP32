'''
--- 實驗 #16-1： 製作一個圖片播放器的網頁 ---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  內建LED → GPIO2
🎯實驗目標
  在網頁上播放 \web\image 裡頭的 .gif 檔案。
'''

import machine
import network
import os
import json
import time

# 引用 microdot 相關模組
from microdot import Microdot, send_file
from microdot.websocket import with_websocket

# --- 0. 基本設定 ---
WIFI_SSID = '910'
WIFI_PASS = '910910910'
WEB_ROOT = '/web'
IMAGE_DIR = f'{WEB_ROOT}/image'

# --- 1. 連接到 WiFi ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print(f'Connecting to network {WIFI_SSID}...')
    wlan.connect(WIFI_SSID, WIFI_PASS)
    while not wlan.isconnected():
        print('.', end='')
        time.sleep(0.5)
print(f'ESP32 IP Address: http://{wlan.ifconfig()[0]}')

# --- 2. 建立 Microdot 應用程式 ---
app = Microdot()

# --- 3. 掃描圖片目錄並建立圖片列表 ---
image_files = []
try:
    # ===== 更正開始 =====
    # MicroPython 的 endswith 不支援元組，所以我們需要逐一檢查
    SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    all_files_in_dir = os.listdir(IMAGE_DIR)
    
    image_files = sorted([
        f for f in all_files_in_dir
        if any(f.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)
    ])
    # ===== 更正結束 =====

    print(f'Found images: {image_files}')
except OSError:
    print(f"Warning: Directory '{IMAGE_DIR}' not found. Please create it and add images.")


# --- 4. 設定 WebSocket 路由 ---
# 注意：WebSocket 路由必須在通用路徑 <path:path> 之前，否則會被當成檔案請求
@app.route('/ws')
@with_websocket
async def image_websocket(request, ws):
    print("WebSocket connection established.")
    
    # 1. 當客戶端連接時，立即發送圖片列表
    try:
        await ws.send(json.dumps({
            'type': 'imageList',
            'data': image_files
        }))
        print("Image list sent to client.")
    except Exception as e:
        print(f"Error sending image list: {e}")

    # 2. 持續監聽 (此專案中客戶端不會發送控制指令，但保留結構以備擴充)
    while True:
        try:
            # 等待客戶端消息，若斷線會拋出異常
            data = await ws.receive()
            # print(f"Received from client: {data}") # 用於調試
        except Exception:
            # 客戶端斷開連接
            print("WebSocket connection closed.")
            break

# --- 5. 設定靜態檔案服務路由 ---
# 這個路由處理所有 /web/ 目錄下的檔案請求，包括 16-1.html 和圖片
@app.route('/<path:path>')
def static_files(request, path):
    # 安全性檢查，防止訪問根目錄以外的檔案
    if '..' in path:
        return 'Not found', 404
    
    # 如果路徑為空或指向根目錄，則預設回傳主頁
    if path == '' or path.endswith('/'):
        path = '16-1.html'

    full_path = f'{WEB_ROOT}/{path}'
    print(f"Serving file: {full_path}")
    
    try:
        # 使用 send_file 來回傳檔案
        return send_file(full_path)
    except OSError:
        # 如果檔案不存在，回傳 404
        return 'Not found', 404

# --- 6. 設定根目錄路由 ---
# 為了方便使用者直接輸入 IP 位址就能看到網頁
@app.route('/')
def index(request):
    print("Serving index page: /web/16-1.html")
    return send_file(f'{WEB_ROOT}/16-1.html')

# --- 7. 啟動伺服器 ---
print("Starting web server...")
try:
    app.run(port=80, debug=True)
except Exception as e:
    print(f"Server failed to start: {e}")