'''
--- 實驗 #17-1： 網頁上顯示可電電阻的數值 ---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  類比輸出模組  → GPIO36。（ADC 腳位，逆時針到底為 0V）
🎯實驗目標
  網頁上顯示可電電阻的數值，透過 websocket 傳送數值。
'''

import machine
import network
import time
import asyncio
from microdot import Microdot, send_file
from microdot.websocket import with_websocket

# 0-1. WIFI 名稱與密碼
WIFI_SSID = 'TP-Link_5E4C_2.4G'
WIFI_PASS = '0976023369'

# --- WiFi 連線 ---
def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('正在連線到 WiFi 網路...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASS)
        while not sta_if.isconnected():
            time.sleep(1)
    
    print('網路設定完成!')
    print('網頁伺服器網址: http://{}'.format(sta_if.ifconfig()[0]))

# --- 硬體設定 ---
# 可變電阻連接到 GPIO36
adc_pin = machine.Pin(36, machine.Pin.IN)
# 建立 ADC 物件
adc = machine.ADC(adc_pin)
# 設定衰減以讀取 0-3.3V 的完整電壓範圍
adc.atten(machine.ADC.ATTN_11DB)

# 0-9. ADC 的平滑處理技術 (10筆移動平均)
readings = [0] * 10
current_adc_value = 0

async def read_adc_smoothed():
    """
    非同步任務：持續讀取 ADC 值並計算移動平均值。
    """
    global current_adc_value
    while True:
        # 讀取原始 ADC 值 (0-4095)
        reading = adc.read()
        
        # 更新讀數列表
        readings.pop(0)
        readings.append(reading)
        
        # 計算平均值
        current_adc_value = sum(readings) // len(readings)
        
        # 短暫休眠，避免過度佔用 CPU
        await asyncio.sleep_ms(50)

# --- Microdot 網頁伺服器設定 ---
# 0-2 & 0-3. 初始化 Microdot
app = Microdot()

# 0-7 & 0-8. WebSocket 路由，用於即時傳輸數據
@app.route('/ws')
@with_websocket
async def websocket_handler(request, ws):
    """
    處理 WebSocket 連線，定期將 ADC 數值傳送給客戶端。
    """
    print("WebSocket 客戶端已連線。")
    while True:
        try:
            # 2. 將可變電阻透過 websocket 傳送數值
            await ws.send(str(current_adc_value))
            # 控制更新頻率
            await asyncio.sleep_ms(200)
        except Exception as e:
            print("WebSocket 錯誤: {}".format(e))
            break
    print("WebSocket 連線已關閉。")

# --- 網頁檔案服務路由 ---
# 根目錄，直接提供主網頁
@app.route('/')
async def index(request):
    return send_file('/web/17-1.html')

# 0-5. 服務 /web 目錄下的靜態檔案
@app.route('/<path:path>')
async def static(request, path):
    """
    提供 /web 目錄下的所有靜態檔案 (如 css, js)。
    """
    if '..' in path:
        # 安全性檢查，防止目錄遍歷
        return '找不到檔案', 404
    try:
        # 確保檔案存在於 /web 目錄下
        full_path = '/web/' + path
        return send_file(full_path)
    except OSError:
        return '找不到檔案', 404

# --- 主執行緒 ---
async def main():
    do_connect()
    # 建立並啟動 ADC 讀取任務
    asyncio.create_task(read_adc_smoothed())
    print('正在啟動 Microdot 伺服器...')
    try:
        # 啟動網頁伺服器，使用標準 HTTP 埠 80
        app.run(port=80)
    except Exception as e:
        print("伺服器錯誤: {}".format(e))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("伺服器已停止。")