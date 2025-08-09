'''
--- 實驗 #20-2-1： 用 ESP32 #1 控制 ESP32 #2 (發射端)---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  內建LED → GPIO2。
  按鈕 → GPIO23（按下時為高電位）
🎯實驗目標
  用 ESP32 #1(發射端)的按鈕去控制 ESP32 #2 (接收端)的LED。
'''
# 檔案名稱：sender.py
# ESP32 #1 (發射端)

import network
import espnow
import machine
import time

# --- 硬體定義 ---
# 按鈕連接到 GPIO23，使用內部上拉電阻
button = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)

# --- ESP-NOW 初始化 ---
# 1. 設定 Wi-Fi 為 STA 模式
sta = network.WLAN(network.STA_IF)
sta.active(True)

# 2. 初始化 ESP-NOW
e = espnow.ESPNow()
e.active(True)

# --- MAC 位址設定 ---
# ESP32 #2 (接收端) 的 MAC 位址
peer_mac_bytes = b'\xD8\x13\x2A\x7A\x72\x98'

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
print("--- ESP32 #1 (發射端) 初始化完成 ---")
print("我的 MAC 位址: " + format_mac(my_mac_bytes))
print("對方的 MAC 位址: " + format_mac(peer_mac_bytes))
print("------------------------------------")
print("初始化完成，等待按鈕按下...")

# --- 主迴圈 ---
last_state = 1  # 按鈕的初始狀態 (1 代表未按下)
while True:
    current_state = button.value()
    
    # 偵測下降緣 (從未按 -> 按下)
    if last_state == 1 and current_state == 0:
        print("按鈕已按下，發送 'toggle' 訊息...")
        
        # 發送訊息給指定的 peer
        try:
            e.send(peer_mac_bytes, b'toggle')
        except OSError as err:
            print("發送失敗:", err)

        # 簡單的防彈跳延遲
        time.sleep_ms(50)
        
    last_state = current_state
    
    # 短暫休眠，降低 CPU 使用率
    time.sleep_ms(10)