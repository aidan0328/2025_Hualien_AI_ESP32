'''
--- 實驗 #20-1： 取得 ESP32 的 MAC Address ---
🖥執行環境：
  MicroPython v1.24.0 + microdot v2.3.3
  ESP32-DevKitC
🔧硬體接線說明
  內建LED → GPIO2。
  按鈕 → GPIO23（按下時為高電位）
🎯實驗目標
  因為要使用到 ESP NOW 的傳輸，所以需要先知道 ESP32 的 MAC Address。
'''

import network
import ubinascii
import time
from machine import Pin

# 雖然這個實驗用不到，但作為良好習慣，可以先定義硬體
# 內建 LED 在 GPIO 2
led = Pin(2, Pin.OUT)



# 1. 初始化 Wi-Fi Station (STA) 介面
#    我們不需要真的連上網路，只需要啟用網路介面來讀取其屬性
wlan_sta = network.WLAN(network.STA_IF)

# 2. 啟用 (Activate) Wi-Fi 介面
#    這一步是必須的，否則可能無法讀取到 MAC 位址
wlan_sta.active(True)

# 3. 檢查介面是否已啟用，並獲取 MAC 位址
if wlan_sta.active():
    # 使用 .config('mac') 來獲取原始的 MAC 位址 (bytes 格式)
    mac_bytes = wlan_sta.config('mac')

    # 4. 將 bytes 格式的 MAC 位址轉換為人類可讀的格式
    #    ubinascii.hexlify(bytes, ':') 可以方便地轉換並用冒號分隔
    mac_str = ubinascii.hexlify(mac_bytes, ':').decode().upper()

    print(f"本機的 MAC Address 是: {mac_str}")

else:
    print("❌ Wi-Fi 介面啟用失敗，無法取得 MAC Address。")

