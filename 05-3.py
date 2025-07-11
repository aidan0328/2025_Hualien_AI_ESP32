# 實驗 #5-3：使用可變電阻調整LED的閃爍速度(CPU優化版)

# 匯入必要的模組
import machine
import time

# --- 硬體接線定義 ---
# LED 模組接腳
RED_PIN = 18
YELLOW_PIN = 19
GREEN_PIN = 21
# 可變電阻 ADC 接腳
ADC_PIN = 36

# --- 實驗參數設定 ---
# 亮滅時間範圍 (單位：毫秒)
MIN_INTERVAL_MS = 100   # 0.1 秒
MAX_INTERVAL_MS = 3000  # 3.0 秒
# ADC 移動平均的取樣數量
MOVING_AVERAGE_SAMPLES = 10

# --- 硬體初始化 ---
# 初始化 LED 接腳為輸出模式
red_led = machine.Pin(RED_PIN, machine.Pin.OUT)
yellow_led = machine.Pin(YELLOW_PIN, machine.Pin.OUT)
green_led = machine.Pin(GREEN_PIN, machine.Pin.OUT)
# 將所有 LED 物件放入一個列表，方便統一操作
leds = [red_led, yellow_led, green_led]

# 初始化 ADC
# GPIO36 是 ADC1_CHANNEL_0
adc = machine.ADC(machine.Pin(ADC_PIN))
# 設定衰減，ATTN_11DB 允許測量完整的 0-3.3V 電壓範圍
adc.atten(machine.ADC.ATTN_11DB)
# 設定解析度為 12-bit，讀取範圍為 0-4095
adc.width(machine.ADC.WIDTH_12BIT)

# --- 輔助函式 ---
def map_value(x, in_min, in_max, out_min, out_max):
    """
    將一個數值從一個範圍線性對應到另一個範圍 (類似 Arduino 的 map() 函式)
    """
    return int(out_min + (out_max - out_min) * (x - in_min) / (in_max - in_min))

# --- 主程式 ---
print("實驗 #5-3 啟動：使用可變電阻調整 LED 閃爍速度")
print("="*40)

# 初始化狀態變數
led_state = 0  # 0 代表燈滅, 1 代表燈亮
last_toggle_time = 0  # 上次切換 LED 狀態的時間戳
adc_readings = []  # 用於存放最近的 ADC 讀數列表
current_blink_interval_ms = MIN_INTERVAL_MS # 當前的亮滅間隔時間

# 進入主迴圈
while True:
    # --- 1. 讀取並平滑化 ADC 數值 ---
    # 讀取當前 ADC 的原始值
    raw_adc_value = adc.read()
    
    # 將新讀數加入列表
    adc_readings.append(raw_adc_value)
    
    # 如果列表超過了指定的樣本數，就移除最舊的一筆資料
    if len(adc_readings) > MOVING_AVERAGE_SAMPLES:
        adc_readings.pop(0)
        
    # 計算移動平均值
    smoothed_adc_value = sum(adc_readings) / len(adc_readings)

    # --- 2. 將 ADC 數值對應到閃爍時間 ---
    # 使用 map_value 函式將平滑後的 ADC 值 (0-4095) 對應到指定的亮滅時間 (100-3000 ms)
    new_blink_interval_ms = map_value(smoothed_adc_value, 0, 4095, MIN_INTERVAL_MS, MAX_INTERVAL_MS)

    # 為了避免洗版，只有在計算出的間隔時間有變化時才更新並列印
    if new_blink_interval_ms != current_blink_interval_ms:
        current_blink_interval_ms = new_blink_interval_ms
        print(f"亮滅時間更新為: {current_blink_interval_ms} ms")

    # --- 3. 非阻塞式閃爍邏輯 ---
    # 取得當前時間 (毫秒)
    current_time = time.ticks_ms()
    
    # 檢查從上次切換狀態到現在是否已經過了足夠長的時間
    # time.ticks_diff() 用於處理 ticks_ms() 的溢位問題，更為安全
    if time.ticks_diff(current_time, last_toggle_time) >= current_blink_interval_ms:
        # 如果時間到了，就更新計時器
        last_toggle_time = current_time
        
        # 切換 LED 狀態 (0 變 1, 1 變 0)
        led_state = 1 - led_state
        
        # 將所有 LED 設定為新的狀態
        for led in leds:
            led.value(led_state)

    # 程式在這裡不會被暫停，可以立即回到迴圈頂部繼續讀取 ADC
    # 這就是非阻塞式設計的核心