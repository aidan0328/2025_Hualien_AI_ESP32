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
import network
import espnow
import machine
import time

# 0. 硬體設定
# 按鈕連接到 GPIO23，使用內部下拉電阻
button = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_DOWN)

# 1. 初始化 Wi-Fi station 模式 (ESP-NOW 運作的必要條件)
sta = network.WLAN(network.STA_IF)
sta.active(True)

# 2. 初始化 ESP-NOW
e = espnow.ESPNow()
e.active(True)

# 3. 新增通訊對象 (Peer)
# 這是 ESP32 #2 (接收端) 的 MAC 地址
peer_mac = b'\x5c\x01\x3b\xe3\x7b\x08'
e.add_peer(peer_mac)


# 獲取並格式化 MAC 位址以便於閱讀
def format_mac(mac_bytes):
    """將 bytes 格式的 MAC 位址轉換為 xx:xx:xx:xx:xx:xx 字串格式"""
    return ':'.join(['{:02x}'.format(b) for b in mac_bytes])

# 獲取本機 (發射端) 的 MAC 位址
my_mac = sta.config('mac')

print("==========================================")
print("ESP-NOW 發射端初始化完成。")
print("本機 (發射端) MAC 位址: {}".format(format_mac(my_mac)))
print("接收端 MAC 位址:       {}".format(format_mac(peer_mac)))
print("==========================================")
print("請按下按鈕以發送 'toggle' 指令。")


# 用於按鈕防彈跳 (debouncing) 的變數
last_button_state = 0

# 4. 主迴圈
while True:
    current_button_state = button.value()

    # 偵測按鈕是否被按下 (從 0 變為 1 的上升緣)
    if current_button_state == 1 and last_button_state == 0:
        message = b'toggle'
        print("按鈕已按下！ 正在發送訊息：{}".format(message))
        
        # 發送訊息給指定的 peer
        try:
            e.send(peer_mac, message)
        except OSError as err:
            print("發送訊息時發生錯誤：{}".format(err))

    last_button_state = current_button_state
    
    # 短暫延遲 20 毫秒以降低 CPU 使用率並做為簡易的防彈跳
    time.sleep_ms(20)