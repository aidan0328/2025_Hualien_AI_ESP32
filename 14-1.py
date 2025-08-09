'''
--- 實驗 #14-1： 透過網頁控制 LED ---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  內建LED → GPIO2
🎯實驗目標
  在網頁上控制 LED 的亮滅。
'''

import network
import machine
from microdot import Microdot, redirect

# --- WiFi 連線設定 ---
WIFI_SSID = '910'
WIFI_PASSWORD = '910910910'

# --- 硬體設定 ---
# 大部分的 ESP32 DevKitC 開發板內建 LED 連接到 GPIO 2
led = machine.Pin(2, machine.Pin.OUT)

# --- 建立 Microdot 應用程式實例 ---
app = Microdot()

# --- 中文 HTML 網頁模板 ---
# 使用字串格式化來動態顯示 LED 狀態
HTML_PAGE = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 LED 控制</title>
    <style>
        body {{ font-family: "Microsoft JhengHei", "PingFang TC", Arial, sans-serif; text-align: center; margin-top: 50px; }}
        h1 {{ color: #333; }}
        p {{ font-size: 1.2em; }}
        .led-state {{
            padding: 5px 15px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
        }}
        .on {{ background-color: #28a745; }}
        .off {{ background-color: #dc3545; }}
        button {{
            padding: 10px 20px;
            font-size: 1em;
            cursor: pointer;
            border: none;
            border-radius: 5px;
            color: white;
        }}
        .btn-on {{ background-color: #007bff; }}
        .btn-off {{ background-color: #6c757d; }}
    </style>
</head>
<body>
    <h1>ESP32 網頁 LED 控制器</h1>
    <p>LED 狀態: <span class="led-state {led_class}">{led_state}</span></p>
    <p>
        <a href="/led/on"><button class="btn-on">開啟 LED</button></a>
         
        <a href="/led/off"><button class="btn-off">關閉 LED</button></a>
    </p>
</body>
</html>
"""

# --- 路由處理函式 ---

@app.route('/')
def index(request):
    """
    處理根目錄請求，顯示主網頁。
    會檢查 LED 的當前狀態並將其渲染到 HTML 中。
    """
    if led.value() == 1:
        led_state = "開啟"
        led_class = "on"
    else:
        led_state = "關閉"
        led_class = "off"
        
    # 回傳 HTML 頁面，並設定內容類型為 text/html
    return HTML_PAGE.format(led_state=led_state, led_class=led_class), 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/led/on')
def led_on(request):
    """
    處理 "/led/on" 請求，將 LED 開啟。
    完成後重定向回主頁。
    """
    led.on()  # 或 led.value(1)
    print("LED 已開啟")
    return redirect('/')

@app.route('/led/off')
def led_off(request):
    """
    處理 "/led/off" 請求，將 LED 關閉。
    完成後重定向回主頁。
    """
    led.off() # 或 led.value(0)
    print("LED 已關閉")
    return redirect('/')

# --- 主程式 ---

def connect_to_wifi(ssid, password):
    """連接到 WiFi 網路的函式"""
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print(f'正在連線到網路 {ssid}...')
        sta_if.active(True)
        sta_if.connect(ssid, password)
        # 等待連接成功
        while not sta_if.isconnected():
            pass
    print('網路設定:', sta_if.ifconfig())
    return sta_if.ifconfig()[0] # 回傳 IP 位址

if __name__ == '__main__':
    try:
        # 連接到 WiFi
        ip = connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)
        print(f"Microdot 伺服器正在 http://{ip} 運行")
        # 啟動網頁伺服器，port=80 是一般的 HTTP 埠
        app.run(port=80)
    except KeyboardInterrupt:
        # 處理 Ctrl+C 停止程式
        print("伺服器已停止。")
        machine.reset()