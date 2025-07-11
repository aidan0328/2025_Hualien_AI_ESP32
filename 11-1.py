# 實驗 #11-1：DHT11 溫濕度感測器資料顯示於 LCD1602 (非阻塞式)
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

from machine import Pin, I2C
import time
import dht
import LCD1602 # 匯入您提供的 LCD 驅動程式

# --- 硬體與常數設定 ---
I2C_SCL_PIN = 17
I2C_SDA_PIN = 16
DHT_DATA_PIN = 5

# 更新間隔 (毫秒)，DHT11 建議至少 1 秒讀取一次
UPDATE_INTERVAL_MS = 2000 

print("程式開始...")
print("初始化硬體...")

# --- 硬體初始化 ---
try:
    # 1. 初始化 I2C 匯流排
    i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)

    # 2. 掃描 I2C 設備以確認 LCD 是否存在並取得位址
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("在 I2C 匯流排上找不到任何設備")
    
    i2c_addr = devices[0]
    print(f"找到 I2C 設備，位址: {hex(i2c_addr)}")

    # 3. 初始化 LCD1602
    # 使用 LCD1602.py 中的 I2cLcd 類別
    lcd = LCD1602.I2cLcd(i2c, i2c_addr, 2, 16)
    lcd.putstr("LCD Initialized\nWaiting for data...")

    # 4. 初始化 DHT11 感測器
    dht_sensor = dht.DHT11(Pin(DHT_DATA_PIN))
    
    # 稍微延遲一下，確保感測器穩定
    time.sleep_ms(1000) 
    
except Exception as e:
    print(f"硬體初始化失敗: {e}")
    # 若初始化失敗，程式將在此結束或進入無限迴圈
    while True:
        pass

print("初始化完成，進入主迴圈...")

# --- 主程式迴圈 ---

# 記錄上一次更新時間的"滴答數" (ticks)
last_update_ticks = time.ticks_ms()

# 清除初始訊息，準備顯示數據
lcd.clear()

while True:
    # --- 非阻塞式計時器 ---
    # 這是實現非阻塞式延遲的核心邏輯
    # 不斷檢查當前時間與上次更新時間的差值
    current_ticks = time.ticks_ms()
    if time.ticks_diff(current_ticks, last_update_ticks) >= UPDATE_INTERVAL_MS:
        
        # 時間到了，重設計時器
        last_update_ticks = current_ticks
        
        # --- 讀取感測器 ---
        try:
            # 觸發感測器進行測量
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            humi = dht_sensor.humidity()

            print(f"讀取成功 - 溫度: {temp}°C, 濕度: {humi}%")
            
            # --- 更新 LCD 顯示 ---
            # 清除舊資料並顯示新資料
            lcd.clear()
            
            # 將溫度顯示在第一行
            lcd.move_to(0, 0)
            lcd.putstr(f"Temp: {temp:>5d} C") # 使用 f-string 格式化字串
            lcd.putchar(chr(223)) # 顯示度(°)符號

            # 將濕度顯示在第二行
            lcd.move_to(0, 1)
            lcd.putstr(f"Humi: {humi:>5d} %")

        except OSError as e:
            # DHT 感測器讀取失敗時的處理
            print(f"DHT 讀取錯誤: {e}")
            lcd.clear()
            lcd.putstr("Sensor Error!")

    # 在此處可以執行其他非阻塞式任務
    # 例如：檢查按鈕、更新網路狀態等
    # 由於本範例沒有其他任務，我們就讓它快速空轉 (pass)
    # 這確保了迴圈不會被 time.sleep() 阻塞
    pass