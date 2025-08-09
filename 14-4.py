'''
--- 實驗 #14-4： 透過網頁或按鈕即時控制 LED  (引入 websocket) ---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  內建LED → GPIO2
  按鈕 → GPIO23（按下時為高電位）
🎯實驗目標
  可以遠端(網頁)或本地端(按鈕)即時控制 LED 的亮滅。。
'''

import machine
import network
import time
import uasyncio as asyncio
import ujson as json
import uos

# 從 microdot 庫中導入需要的模組
from microdot import Microdot, send_file
from microdot.websocket import with_websocket

# --- 1. 基本設定 ---
WIFI_SSID = "910"
WIFI_PASS = "910910910"
SERVER_PORT = 80 # 使用 80 port，這樣瀏覽器就不用輸入 port 號

# 硬體設定
LED_PIN = 2
BUTTON_PIN = 23

# 初始化硬體
# machine 模組沒有 toggle(), 我們需要手動實現
led = machine.Pin(LED_PIN, machine.Pin.OUT)
# 按下時為高電位，所以平時用 PULL_DOWN 保持低電位
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# --- 2. 全域變數 ---
# 建立一個集合(set)來儲存所有活躍的 WebSocket 客戶端
# 使用 set 的好處是新增和移除的效率高，且能自動處理重複
g_ws_clients = set()

# --- 3. 網路連線 ---
def connect_wifi():
    """連接到指定的 WiFi 網路"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"正在連接到 WiFi: {WIFI_SSID}...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        # 等待連線成功
        max_wait = 15
        while not wlan.isconnected() and max_wait > 0:
            max_wait -= 1
            print(".", end="")
            time.sleep(1)

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\nWiFi 已連接, IP 位址: http://{ip}")
        return ip
    else:
        print("\nWiFi 連接失敗")
        return None

# --- 4. WebSocket 相關函式 ---
async def broadcast_led_state():
    """廣播 LED 當前狀態給所有 WebSocket 客戶端"""
    current_state = led.value()
    message = json.dumps({
        'type': 'state',
        'value': current_state # 1 代表亮, 0 代表滅
    })
    
    # 複製一份集合來遍歷，避免在遍歷時修改集合大小
    for ws in g_ws_clients.copy():
        try:
            await ws.send(message)
        except Exception as e:
            print(f"傳送失敗，移除客戶端: {e}")
            g_ws_clients.remove(ws)

def toggle_led():
    """切換 LED 狀態"""
    led.value(not led.value())
    print(f"LED 狀態切換為: {'ON' if led.value() else 'OFF'}")


# --- 5. Microdot 網頁伺服器設定 ---
app = Microdot()

@app.route('/')
def index(request):
    """提供主網頁"""
    print("請求主頁面 / ...")
    # 使用 send_file 來發送網頁，它會自動處理 MIME 類型
    return send_file('/web/14-4.html', content_type="text/html; charset=utf-8")

@app.route('/ws')
@with_websocket
async def websocket_handler(request, ws):
    """處理 WebSocket 連線"""
    print(f"WebSocket 連線建立: {request.client_addr}")
    g_ws_clients.add(ws)

    try:
        # 1. 當客戶端一連上，立刻傳送當前的 LED 狀態
        await broadcast_led_state()

        # 2. 進入迴圈，等待來自客戶端的訊息
        while True:
            message = await ws.receive()
            print(f"收到 WebSocket 訊息: {message}")
            if message == 'toggle':
                toggle_led()
                # 狀態改變後，廣播給所有客戶端
                await broadcast_led_state()

    except Exception as e:
        print(f"WebSocket 連線錯誤: {e}")
    finally:
        # 3. 當連線關閉或發生錯誤時，從集合中移除客戶端
        print(f"WebSocket 連線關閉: {request.client_addr}")
        g_ws_clients.remove(ws)


# --- 6. 硬體監聽任務 (按鈕) ---
async def button_monitor():
    """一個獨立的非同步任務，專門監控實體按鈕"""
    last_state = 0
    while True:
        current_state = button.value()
        # 偵測按鈕被按下 (從 0 -> 1)
        if current_state == 1 and last_state == 0:
            # 簡單的去抖動
            await asyncio.sleep_ms(20)
            if button.value() == 1:
                print("實體按鈕被按下！")
                toggle_led()
                # 廣播新狀態給所有網頁客戶端
                await broadcast_led_state()
                # 等待按鈕釋放
                while button.value() == 1:
                    await asyncio.sleep_ms(20)
        
        last_state = current_state
        # 稍微延遲，釋放 CPU 給其他任務
        await asyncio.sleep_ms(50)

# --- 7. 主執行緒 ---
async def main():
    # 確保 web 目錄存在
    try:
        uos.mkdir('web')
        print("已建立 /web 目錄")
    except OSError:
        # 目錄已存在
        pass

    # 連接 WiFi
    if not connect_wifi():
        return

    # 建立按鈕監聽任務
    asyncio.create_task(button_monitor())
    
    # 啟動 Microdot 伺服器
    print(f"伺服器啟動於 0.0.0.0:{SERVER_PORT}")
    try:
        # 使用 start_server 而不是 run，以便與其他異步任務並行
        await app.start_server(port=SERVER_PORT, debug=True)
    except Exception as e:
        print(f"伺服器啟動失敗: {e}")
        # 重啟開發板
        machine.reset()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程式被手動中斷")