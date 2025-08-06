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
import network
import espnow
import machine
import time

# 0. 硬體設定
# 內建 LED 通常連接到 GPIO2
led = machine.Pin(2, machine.Pin.OUT)
led.off()  # 初始狀態設為關閉

# 1. 初始化 Wi-Fi station 模式 (ESP-NOW 運作的必要條件)
sta = network.WLAN(network.STA_IF)
sta.active(True)

# 2. 初始化 ESP-NOW
e = espnow.ESPNow()
e.active(True)

# --- 新增的程式碼區塊 ---
# 預期會接收訊息的發射端 MAC 位址
# 注意：在接收端，我們不需要 add_peer()，但知道發射端的 MAC 有助於除錯
sender_mac_expected = b'\xF4\x65\x0B\xAD\x99\xA0' # <-- 請填入 ESP32 #1 的實際 MAC 位址

def format_mac(mac_bytes):
    """將 bytes 格式的 MAC 位址轉換為 xx:xx:xx:xx:xx:xx 字串格式"""
    return ':'.join(['{:02x}'.format(b) for b in mac_bytes])

# 獲取本機 (接收端) 的 MAC 位址
my_mac = sta.config('mac')

print("==========================================")
print("ESP-NOW 接收端初始化完成。")
print("本機 (接收端) MAC 位址: {}".format(format_mac(my_mac)))
# 為了清楚起見，也顯示我們預期從哪個發射端接收訊息
print("預期發射端 MAC 位址: {}".format(format_mac(sender_mac_expected)))
print("==========================================")
print("等待訊息中...")
# --- 新增的程式碼區塊結束 ---


# 3. 主迴圈
while True:
    # 等待接收訊息
    host_mac, msg = e.recv()
    
    # 檢查是否真的收到了訊息 (超時會返回 None)
    if msg:
        # 將收到的 bytes MAC 位址格式化後再列印
        print("收到來自 {} 的訊息，內容：{}".format(format_mac(host_mac), msg))
        
        # 如果收到的訊息是 'toggle'
        if msg == b'toggle':
            print("收到 'toggle' 指令，正在切換 LED 狀態。")
            # 執行 LED 狀態切換
            led.value(not led.value())
        else:
            print("收到未知的指令。")