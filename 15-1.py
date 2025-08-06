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
import time
import asyncio
import network
import json
from microdot import Microdot, send_file
from microdot.websocket import with_websocket

# --- WiFi 設定 ---
WIFI_SSID = 'TP-Link_5E4C_2.4G'
WIFI_PASSWORD = '0976023369'
# -----------------

# --- 硬體設定 ---
# 使用 PWM 來控制 LED 亮度
# 頻率 1000Hz 可以避免閃爍
led_pwm = machine.PWM(machine.Pin(2), freq=1000)
# -----------------

# --- 全域變數與狀態管理 ---
clients = set()  # 存放所有連接的 websocket 客戶端
# 使用字典來統一管理 LED 狀態
led_state = {
    "state": "off",      # 'on' 或 'off'
    "brightness": 100    # 亮度百分比 (5-100)
}
# 用於確保同時只有一個任務在修改 LED 狀態
state_lock = asyncio.Lock()

# --- WiFi 連線函數 ---
async def connect_wifi():
    """非同步連線到 WiFi"""
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    if not sta_if.isconnected():
        print("正在連線到 WiFi...")
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        while not sta_if.isconnected():
            print(".", end="")
            await asyncio.sleep(0.5)
    print("\nWiFi 已連線!")
    #print("網路設定:", sta_if.ifconfig())
    print(f'ESP32 IP Address: http://{sta_if.ifconfig()[0]}')
# --- LED 控制與廣播函數 ---
async def update_led_and_broadcast():
    """根據全域 led_state 更新 LED 硬體狀態並廣播給所有客戶端"""
    async with state_lock:
        state_str = json.dumps(led_state)
        print("更新並廣播狀態: ", state_str)

        if led_state["state"] == "on":
            # 將 5-100 的百分比對應到 0-1023 的 duty cycle
            # 5% -> 51, 100% -> 1023
            duty = int((led_state["brightness"] / 100) * 1023)
            # 確保 duty cycle 不會低於最小值
            if duty < 51: duty = 51 
            led_pwm.duty(duty)
        else:
            led_pwm.duty(0) # 關閉 LED
        
        # 廣播給所有客戶端
        for ws in list(clients):
            try:
                await ws.send(state_str)
            except Exception as e:
                print("傳送失敗，移除客戶端: ", e)
                clients.remove(ws)

# --- Microdot 網頁伺服器設定 ---
app = Microdot()

# --- WebSocket 路由 ---
@app.route('/ws')
@with_websocket
async def ws_handler(request, ws):
    """處理 WebSocket 連線與訊息"""
    print("WebSocket 客戶端已連線")
    clients.add(ws)
    try:
        # 連線後立即傳送目前狀態
        await ws.send(json.dumps(led_state))
        
        # 持續接收客戶端訊息
        while True:
            data = await ws.receive()
            try:
                command = json.loads(data)
                action = command.get('action')
                print("收到指令: ", command)
                
                async with state_lock:
                    state_changed = False
                    if action == 'on' and led_state['state'] == 'off':
                        led_state['state'] = 'on'
                        state_changed = True
                    elif action == 'off' and led_state['state'] == 'on':
                        led_state['state'] = 'off'
                        state_changed = True
                    elif action == 'toggle':
                        led_state['state'] = 'off' if led_state['state'] == 'on' else 'on'
                        state_changed = True
                    elif action == 'set_brightness':
                        value = command.get('value')
                        if isinstance(value, int) and 5 <= value <= 100:
                            if led_state['brightness'] != value:
                                led_state['brightness'] = value
                                state_changed = True
                
                if state_changed:
                    await update_led_and_broadcast()

            except (ValueError, KeyError) as e:
                print("無效的 WebSocket 訊息: ", data, e)

    except Exception as e:
        print("WebSocket 連線關閉: ", e)
    finally:
        if ws in clients:
            clients.remove(ws)
            print("WebSocket 客戶端已移除")

# --- 網頁檔案伺服器路由 ---
@app.route('/')
async def index(request):
    """提供主網頁"""
    return send_file('/web/15-1.html')

@app.route('/<path:path>')
async def static(request, path):
    """提供 /web 資料夾中的靜態檔案"""
    try:
        return send_file('/web/' + path)
    except Exception:
        return 'Not found', 404

# --- 主程式 ---
async def main():
    await connect_wifi()
    
    print('啟動 Microdot 伺服器...')
    
    # 伺服器啟動前，先根據初始狀態設定一次LED
    await update_led_and_broadcast()
    
    try:
        await app.start_server(port=80, debug=True)
    except Exception as e:
        print("伺服器啟動失敗: ", e)

# --- 程式進入點 ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程式被手動中斷") 