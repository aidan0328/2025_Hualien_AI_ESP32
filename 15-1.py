'''
--- 實驗 #15-1： 透過網頁即時改變 LED 的亮滅與亮度 ---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  內建LED → GPIO2
🎯實驗目標
  可以遠端(網頁)即時改變 LED 的亮滅與亮度。
'''

import machine
import network
import time
import os
import json
import asyncio
from microdot import Microdot, send_file
from microdot.websocket import with_websocket

# --- 0. 基本設定 ---
# 0-0. 手動實現 toggle 功能
def toggle_pin(p):
    p.value(not p.value())

# 0-1. WIFI 名稱與密碼
WIFI_SSID = '910'
WIFI_PASS = '910910910'

# 硬體設定
LED_PIN = 2
led_pin = machine.Pin(LED_PIN, machine.Pin.OUT)
# 使用 PWM 控制 LED 亮度，頻率設定為 1000 Hz
led_pwm = machine.PWM(led_pin, freq=1000, duty_u16=0)

# --- 全域變數，用於管理狀態與連線 ---
websockets = set()
# 初始狀態：滅
led_state = {
    "is_on": False,
    "brightness": 0  # 使用 0-100 的百分比來表示亮度
}

# --- 1. WiFi 連線 ---
def connect_wifi():
    """連線到指定的 WiFi 網路"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('正在連接網路...')
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep_ms(500)
    
    ip_address = wlan.ifconfig()[0]
    print('伺服器的網址是 http://{}:80'.format(ip_address))
    return ip_address

# --- 2. Microdot 伺服器設定 ---
app = Microdot()

async def broadcast_state():
    """廣播 LED 的目前狀態給所有 websocket 客戶端"""
    state_msg = json.dumps(led_state)
    
    for ws in list(websockets):
        try:
            await ws.send(state_msg)
        except Exception:
            websockets.remove(ws)
            print("一個 WebSocket 客戶端已移除")

def update_led():
    """根據 led_state 更新 PWM 輸出"""
    if led_state["is_on"]:
        # 將 5%-100% 的亮度對應到 duty_u16 的範圍 (0-65535)
        # 5% -> 3277, 100% -> 65535
        duty = int(led_state["brightness"] / 100 * 65535)
        led_pwm.duty_u16(duty)
    else:
        led_pwm.duty_u16(0)
    print("更新 LED 狀態: is_on={}, brightness={}%, duty_u16={}".format(
        led_state["is_on"], led_state["brightness"], led_pwm.duty_u16()
    ))

# --- 4. 路由設定 ---
# 0-8. 將 WebSocket 路由放在最前面
@app.route('/ws')
@with_websocket
async def websocket_handler(request, ws):
    """處理 WebSocket 連線與訊息"""
    print("一個 WebSocket 客戶端已連線")
    websockets.add(ws)
    
    # 新客戶端連線時，立即發送目前的 LED 狀態
    await ws.send(json.dumps(led_state))
    
    try:
        while True:
            data_str = await ws.receive()
            try:
                data = json.loads(data_str)
                action = data.get('action')

                if action == 'on':
                    led_state["is_on"] = True
                    if led_state["brightness"] < 5: # 如果亮度為0，預設為100%
                        led_state["brightness"] = 100
                elif action == 'off':
                    led_state["is_on"] = False
                elif action == 'toggle':
                    led_state["is_on"] = not led_state["is_on"]
                    if led_state["is_on"] and led_state["brightness"] < 5:
                        led_state["brightness"] = 100
                elif action == 'brightness':
                    # 確保亮度在 5 到 100 之間
                    brightness = int(data.get('value', 100))
                    led_state["brightness"] = max(5, min(100, brightness))

                update_led()
                await broadcast_state()

            except (ValueError, KeyError) as e:
                print("收到了無效的 WebSocket 訊息: {}, 錯誤: {}".format(data_str, e))

    except Exception as e:
        print("WebSocket 連線異常關閉: {}".format(e))
    finally:
        websockets.remove(ws)
        print("一個 WebSocket 客戶端已離線")

@app.route('/')
async def index(request):
    """處理根目錄請求，發送網頁"""
    return send_file('/web/15-1.html')

@app.route('/<path:path>')
async def static_files(request, path):
    """處理靜態檔案請求"""
    full_path = '/web/' + path
    try:
        return send_file(full_path)
    except OSError:
        return 'Not Found', 404

# --- 5. 主程式執行 ---
if __name__ == '__main__':
    try:
        connect_wifi()
        update_led() # 確保啟動時LED是滅的
        print("Microdot 伺服器已啟動")
        # 使用 asyncio.run 來啟動 Microdot，這是 v2.x 的推薦方式
        asyncio.run(app.start_server(port=80, debug=True))
    except KeyboardInterrupt:
        print("伺服器已手動停止")
        machine.reset()