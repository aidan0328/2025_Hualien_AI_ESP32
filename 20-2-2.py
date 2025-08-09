'''
--- 實驗 #20-2-2： 用 ESP32 #1 控制 ESP32 #2 (接收端)---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  內建LED → GPIO2。
  按鈕 → GPIO23（按下時為高電位）
🎯實驗目標
  用 ESP32 #1(發射端)的按鈕去控制 ESP32 #2 (接收端)的LED。
'''

# 檔案名稱：receiver.py
# ESP32 #2 (接收端)

import network
import espnow
import machine

# --- 硬體定義 ---
# 內建 LED 連接到 GPIO2
led = machine.Pin(2, machine.Pin.OUT)
led.value(0) # 預設關閉 LED

# --- ESP-NOW 初始化 ---
# 1. 設定 Wi-Fi 為 STA 模式
sta = network.WLAN(network.STA_IF)
sta.active(True)

# 2. 初始化 ESP-NOW
e = espnow.ESPNow()
e.active(True)

# --- MAC 位址設定 ---
# ESP32 #1 (發射端) 的 MAC 位址
peer_mac_bytes = b'\xF4\x65\x0B\xAD\x99\xA0'

# 輔助函式：將 bytes 格式的 MAC 位址轉為可讀字串
def format_mac(mac_bytes):
    mac_str = ""
    for i, byte in enumerate(mac_bytes):
        hex_byte = '{:02X}'.format(byte)
        mac_str += hex_byte
        if i < len(mac_bytes) - 1:
            mac_str += ":"
    return mac_str

# 註冊對方
try:
    e.add_peer(peer_mac_bytes)
    print("已成功註冊對方。")
except OSError as e:
    print("註冊對方失敗:", e)

# 顯示自己的 MAC 位址
my_mac_bytes = sta.config('mac')
print("--- ESP32 #2 (接收端) 初始化完成 ---")
print("我的 MAC 位址: " + format_mac(my_mac_bytes))
print("對方的 MAC 位址: " + format_mac(peer_mac_bytes))
print("------------------------------------")
print("初始化完成，等待接收訊息...")

# --- 主迴圈 ---
while True:
    # 等待接收訊息 (e.recv() 是阻塞的)
    host, msg = e.recv()
    
    # 如果有收到訊息
    if msg:
        # 將收到的 host (bytes) 和 msg (bytes) 轉為字串顯示
        print("從 " + format_mac(host) + " 收到訊息: " + str(msg, 'utf-8'))
        
        # 如果收到的訊息是 'toggle'
        if msg == b'toggle':
            # 實現 toggle 功能：讀取目前狀態，然後設定為相反的狀態
            current_state = led.value()
            new_state = not current_state
            led.value(new_state)
            
            # 顯示 LED 的新狀態
            if new_state:
                print("LED 已開啟。")
            else:
                print("LED 已關閉。")