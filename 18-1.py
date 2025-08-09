'''
--- 實驗 #18-1： 網頁改變  WS2812 的顏色 ---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  兩顆 WS2812B  → GPIO2
🎯實驗目標
  網頁改變 WS2812 的顏色，透過 websocket 傳送數值。
'''
import machine
import network
import time
import neopixel
import asyncio
import json
from microdot import Microdot, send_file
from microdot.websocket import with_websocket

# --- WiFi 連線設定 ---
WIFI_SSID = '910'
WIFI_PASS = '910910910'
WEB_ROOT = '/web'

# --- 硬體設定 ---
WS2812_PIN = 2
NUM_LEDS = 2

# 初始化 NeoPixel (WS2812)
# 建立 NeoPixel 物件
np = neopixel.NeoPixel(machine.Pin(WS2812_PIN), NUM_LEDS)
print('WS2812 LED 已在 GPIO {} 上初始化'.format(WS2812_PIN))

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

# --- Microdot 網頁伺服器設定 ---
app = Microdot()

def hex_to_rgb(hex_color):
    """將 #RRGGBB 格式的十六進位顏色字串轉換為 (r, g, b) 元組"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# --- WebSocket 路由 ---
@app.route('/ws')
@with_websocket
async def websocket_handler(request, ws):
    """
    處理 WebSocket 連線，接收顏色控制指令並更新 LED。
    """
    print("WebSocket 客戶端已連線。")
    while True:
        try:
            # 等待從客戶端接收訊息
            data = await ws.receive()
            
            # 解析 JSON 指令
            try:
                command = json.loads(data)
                led_index = command.get('led_index')
                color_hex = command.get('color')

                if led_index is not None and color_hex is not None:
                    # 1. 將顏色值顯示在 WS2812 上
                    if 0 <= led_index < NUM_LEDS:
                        color_rgb = hex_to_rgb(color_hex)
                        print('設定 LED {} 的顏色為 {}'.format(led_index, color_rgb))
                        np[led_index] = color_rgb
                        np.write() # 將顏色數據寫入 LED 燈條
                    else:
                        print('錯誤：無效的 LED 索引值 {}'.format(led_index))

            except (ValueError, TypeError) as e:
                print('收到了無效的 JSON 格式: {}'.format(e))
                
        except Exception as e:
            print("WebSocket 錯誤: {}".format(e))
            break
    print("WebSocket 連線已關閉。")

# --- 網頁檔案服務路由 ---
@app.route('/')
async def index(request):
    return send_file('/web/18-1.html')

@app.route('/<path:path>')
async def static(request, path):
    if '..' in path:
        return '找不到檔案', 404
    try:
        full_path = '/web/' + path
        return send_file(full_path)
    except OSError:
        return '找不到檔案', 404

# --- 主執行緒 ---
def main():
    # 初始時關閉所有 LED
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()
    
    do_connect()
    
    print('正在啟動 Microdot 伺服器...')
    try:
        app.run(port=80)
    except Exception as e:
        print("伺服器錯誤: {}".format(e))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("伺服器已停止。")