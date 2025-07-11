# 🧪 實驗 #4-2：平滑化可變電阻的 ADC 類比輸入值
# -----------------------------------------------------
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC
# 硬體接線：可變電阻中間腳位 -> GPIO36
#           可變電阻兩側腳位 -> 3.3V 和 GND
#
# 實驗目標：
# 1. 讀取 GPIO36 的 ADC 原始值。
# 2. 使用移動平均法（Moving Average）對 ADC 值進行平滑處理。
# 3. 平滑窗口大小設定為 10 筆。
# 4. 將「原始值」與「平滑值」輸出至序列埠，以便 Arduino IDE 的序列繪圖器觀察。
# -----------------------------------------------------

from machine import Pin, ADC
import utime

# --- 參數設定 ---
ADC_PIN_NUM = 36      # 可變電阻連接的 ADC 腳位 (GPIO36 是 ADC1_CHANNEL_0)
SAMPLES_COUNT = 10    # 用於計算移動平均的樣本數量
LOOP_DELAY_MS = 50    # 每次讀取之間的延遲時間 (毫秒)

# --- 硬體初始化 ---
# 初始化 ADC
# ESP32 的 ADC 腳位不需要預先設定為輸入模式，直接建立 ADC 物件即可
try:
    adc_pin = Pin(ADC_PIN_NUM)
    adc = ADC(adc_pin)
    
    # 設定 ADC 的衰減（attenuation）和位元寬度（bit width）
    # ATTN_11DB: 提供 0V 到 3.3V 的完整輸入電壓範圍，這是最常用的設定
    adc.atten(ADC.ATTN_11DB)
    
    # WIDTH_12BIT: 解析度為 12 位元 (數值範圍 0-4095)
    adc.width(ADC.WIDTH_12BIT)
    
except ValueError:
    print(f"錯誤：腳位 {ADC_PIN_NUM} 無法被設定為 ADC。請確認您的 ESP32 板型與腳位。")
    # 停止程式，因為 ADC 無法使用
    # 在嵌入式系統中，可以進入一個死循環或重啟
    while True:
        pass

# --- 資料儲存 ---
# 建立一個列表來儲存最近的 ADC 讀值歷史
readings_history = []

# --- 主程式開始 ---

# 為了讓 Arduino IDE 的「序列繪圖器」能正確顯示圖例 (Legend)
# 我們在迴圈開始前先印出標頭。
# 繪圖器會自動將逗號分隔的第一個值視為 "原始值"，第二個值視為 "平滑值"。
print("原始值,平滑值")

while True:
    # 1. 讀取原始 ADC 值
    # adc.read() 會回傳一個 0-4095 之間的整數
    raw_value = adc.read()

    # 2. 更新歷史讀值列表
    # 將最新的讀值加入到列表的尾端
    readings_history.append(raw_value)

    # 3. 維護列表長度
    # 如果列表中的樣本數超過了我們設定的 SAMPLES_COUNT，
    # 就從列表的最前面 (最舊的資料) 移除一筆。
    if len(readings_history) > SAMPLES_COUNT:
        readings_history.pop(0) # pop(0) 移除索引為 0 的元素

    # 4. 計算平滑後的值 (移動平均值)
    # 將列表中所有的值相加，再除以列表的長度 (即樣本數)
    # 使用整數除法 // 來確保結果是整數
    smoothed_value = sum(readings_history) // len(readings_history)

    # 5. 輸出結果到序列埠
    # 格式為 "值1,值2"，並以換行結束，這是序列繪圖器要求的格式。
    print("{},{}".format(raw_value, smoothed_value))
    
    # 6. 短暫延遲
    # 避免洗版，並讓序列繪圖器有足夠的時間更新
    utime.sleep_ms(LOOP_DELAY_MS)