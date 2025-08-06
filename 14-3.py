'''
--- 實驗 #14-3： 透過網頁即時控制 LED (引入 websocket) ---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  內建LED → GPIO2
🎯實驗目標
  在網頁上「即時」控制 LED 的亮滅。，網頁上只有一個 Toggle 按鈕。
'''

import machine
import network
import time

# 匯入 Microdot, send_file 和 with_websocket
from microdot import Microdot, send_file
from microdot.websocket import with_websocket

# --- 硬體設定 ---
led = machine.Pin(2, machine.Pin.OUT)
led_state = 0  # 初始狀態為 0 (關)
led.value(led_state)

# --- WIFI 設定 ---
WIFI_SSID = "TP-Link_5E4C_2.4G"
WIFI_PASS = "0976023369"

# --- WiFi 連線函式 ---
def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('正在連接到WiFi網路...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASS)
        while not sta_if.isconnected():
            time.sleep(1)
    
    print('網路已連接, IP位址: ' + sta_if.ifconfig()[0])
    return sta_if.ifconfig()[0]

# --- Microdot 網頁伺服器設定 ---
app = Microdot()

@app.route('/')
def index(request):
    """
    提供主控制頁面 14-3.html。
    """
    print("請求主頁面...")
    return send_file('web/14-3.html')

# **重要**：WebSocket 路由必須在任何通用的檔案路由之前定義
@app.route('/ws')
@with_websocket
async def websocket_handler(request, ws):
    """
    處理 WebSocket 連線和訊息。
    """
    print('WebSocket 連線已建立')
    try:
        while True:
            # 等待從客戶端接收訊息
            message = await ws.receive()
            
            if message == 'toggle':
                global led_state
                # 手動實現 toggle
                led_state = 1 - led_state
                led.value(led_state)
                
                status_msg = 'ON' if led_state == 1 else 'OFF'
                print('WebSocket 指令接收: 切換 LED, 目前狀態: ' + status_msg)
                
                # 將新的狀態回傳給客戶端
                await ws.send('state: ' + status_msg)
            else:
                # 如果收到未知的指令，也回傳訊息
                await ws.send('未知的指令: ' + message)

    except Exception as e:
        # 捕捉連線中斷等錯誤
        print('WebSocket 錯誤: ' + str(e))
        
# --- 主程式執行區塊 ---
try:
    # 1. 連接到 WiFi
    ip = do_connect()
    
    # 2. 啟動 Microdot 伺服器
    print("網頁伺服器已啟動於 http://" + ip)
    app.run(port=80, debug=True)

except Exception as e:
    print("發生錯誤:", e)
    machine.reset()