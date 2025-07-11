# ----------------------------------------------------------------
# 實驗 #10-1： 偵測溫度與溼度 (非阻塞式版本)
#
# 說明：
# 本程式使用非阻塞式 (non-blocking) 的方式，
# 週期性地從 DHT11 感測器讀取溫度與濕度，
# 並將結果列印到 REPL 互動環境中。
#
# 所謂「非阻塞式」是指程式主迴圈不會因為等待而被卡住，
# 而是透過不斷檢查當前時間與上次執行時間的差額，
# 來決定是否執行讀取感測器的任務。
#
# 執行環境：
#   - MicroPython v1.24.0
#   - ESP32-DevKitC
#
# 硬體接線：
#   - DHT11 (Data Pin) → ESP32 (GPIO5)
# ----------------------------------------------------------------

import dht
from machine import Pin
import time

# --- 硬體與常數設定 ---

# 定義 DHT11 感測器連接的 GPIO 接腳
DHT_PIN_NUMBER = 5

# 定義讀取感測器的時間間隔 (單位：毫秒)
# DHT11 的官方資料建議每次讀取至少間隔 1-2 秒，以確保數據穩定
READ_INTERVAL_MS = 2000  # 設定為 2000 毫秒 (2秒)

# --- 初始化 ---

# 1. 初始化 GPIO 接腳
dht_pin = Pin(DHT_PIN_NUMBER, Pin.IN, Pin.PULL_UP)

# 2. 初始化 DHT11 感測器物件
#    將設定好的 Pin 物件傳入 dht.DHT11()
dht_sensor = dht.DHT11(dht_pin)

# 3. 初始化非阻塞計時器所需的變數
#    `last_read_time` 用來記錄上一次成功讀取感測器的時間點
last_read_time = 0

# --- 主程式 ---

print("程式已啟動。開始偵測溫度與溼度...")
print(f"硬體接腳: GPIO{DHT_PIN_NUMBER}")
print(f"更新頻率: 每 {READ_INTERVAL_MS / 1000} 秒一次 (非阻塞式)")
print("-" * 20)

# 進入主迴圈，程式會永遠在這裡執行
while True:
    # 取得當前的時間 (單位：毫秒)
    current_time = time.ticks_ms()

    # 檢查距離上次讀取是否已超過設定的間隔時間
    # time.ticks_diff() 可以正確處理計時器溢位 (rollover) 的問題，比單純相減更安全
    if time.ticks_diff(current_time, last_read_time) >= READ_INTERVAL_MS:
        
        # 如果時間到了，就執行以下任務：
        
        # 1. 更新上次讀取時間為現在的時間
        last_read_time = current_time

        # 2. 嘗試讀取感測器數據
        try:
            # 觸發感測器進行測量 (必要步驟)
            dht_sensor.measure()
            
            # 從感測器物件中取得溫度和濕度
            temperature = dht_sensor.temperature()  # 單位: °C
            humidity = dht_sensor.humidity()        # 單位: %

            # 3. 將讀取到的數據格式化並列印出來
            print(f"溫度: {temperature}°C, 濕度: {humidity}%")

        except OSError as e:
            # DHT 感測器有時會讀取失敗，這是正常現象。
            # 使用 try-except 捕捉這個錯誤，避免程式因此中斷。
            print(f"錯誤：無法從 DHT11 感測器讀取數據. {e}")

    # (在這個位置，可以加入其他非阻塞的程式碼，它們會持續執行，不會被感測器讀取等待所影響)
    # pass # 此處 pass 僅為示意