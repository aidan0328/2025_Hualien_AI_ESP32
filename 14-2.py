'''
--- 實驗 #14-2： 透過網頁控制 LED (Toggle) ---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  內建LED → GPIO2
🎯實驗目標
  在網頁上控制 LED 的亮滅，網頁上只有一個 Toggle 按鈕。
'''

# MicroPython v1.24.0 + microdot v2.3.3
# ESP32-DevKitC

import machine
import network
import time

# 依照您的要求，從提供的 microdot 函式庫結構中匯入
# 這次我們需要 send_file 來提供網頁檔案
from microdot import Microdot, send_file

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
    根路由，提供 14-2.html 網頁。
    """
    print("請求主頁面...")
    # 使用 send_file 從 /web 目錄提供檔案
    return send_file('web/14-2.html')

@app.route('/led/toggle', methods=['POST'])
def led_toggle(request):
    """
    處理切換 LED 狀態的請求。
    """
    global led_state
    # machine.Pin 沒有 toggle()，所以我們手動實現
    led_state = 1 - led_state
    led.value(led_state)
    
    # 使用字串串接，而非 f-string
    status_msg = '開啟' if led_state == 1 else '關閉'
    print('指令接收：切換 LED，目前狀態: ' + status_msg)
    
    # 傳回一個簡單的成功回應，狀態碼 204 (No Content) 表示成功但無須回傳內容
    return '', 204

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