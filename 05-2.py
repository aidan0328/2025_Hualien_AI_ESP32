# ----------------------------------------------------------------------
# 實驗 #5-2：使用可變電阻調整LED的閃爍速度
#
# 說明：
# 透過讀取 GPIO36 上的可變電阻 ADC 值，
# 並使用10筆移動平均法進行平滑處理，
# 將 ADC 值 (0-4095) 線性映射到一個時間區間 (0.1秒 - 3.0秒)，
# 以此時間來控制三顆 LED 同時亮滅的閃爍速度。
#
# 執行環境：
# MicroPython v1.24.0
# ESP32-DevKitC
#
# 硬體接線：
# - 可變電阻 -> GPIO36 (ADC1_CH0)
# - 紅色 LED -> GPIO18
# - 黃色 LED -> GPIO19
# - 綠色 LED -> GPIO21
# ----------------------------------------------------------------------

import machine
import time
from collections import deque

# --- 1. 硬體腳位與參數設定 ---

# ADC 設定
# 可變電阻連接到 GPIO36 (ADC1_CH0)
pot_pin = machine.Pin(36)
adc = machine.ADC(pot_pin)
# 設定衰減，讓 ADC 可以讀取 0-3.3V 的電壓
# ATTN_11DB 對應的電壓範圍約為 0-3.6V，這是 ESP32 的標準設定
adc.atten(machine.ADC.ATTN_11DB)
# 設定 ADC 解析度為 12-bit，讀取值範圍 0-4095
adc.width(machine.ADC.WIDTH_12BIT)

# LED 腳位設定
# 將所有 LED 的 GPIO 編號放入一個列表中，方便統一控制
led_pins_numbers = [18, 19, 21]  # [R, Y, G]
# 使用列表推導式 (List Comprehension) 快速建立 Pin 物件列表
leds = [machine.Pin(pin, machine.Pin.OUT) for pin in led_pins_numbers]

# 移動平均 (Moving Average) 設定
# 建立一個最大長度為10的 deque，用於存放最近10筆ADC讀值
# deque 在新增/移除兩端元素時效率比 list 更高
adc_readings = deque((), 10)
NUM_SAMPLES = 10

# 時間映射 (Mapping) 參數設定
ADC_MIN = 0
ADC_MAX = 4095
TIME_MIN = 0.1  # 逆時針到底 (ADC值最小) 的亮滅時間 (秒)
TIME_MAX = 3.0  # 順時針到底 (ADC值最大) 的亮滅時間 (秒)


# --- 2. 輔助函式 ---

def map_value(x, in_min, in_max, out_min, out_max):
    """
    線性映射函式：將一個數字從一個範圍轉換到另一個範圍。
    (俗稱的 map() 函式)
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def get_smoothed_adc():
    """
    讀取 ADC 值並進行移動平均平滑處理。
    """
    # 讀取當前的 ADC 值
    current_reading = adc.read()
    
    # 將新讀值加入 deque，如果已滿，最舊的會自動被擠掉
    adc_readings.append(current_reading)
    
    # 計算 deque 中所有值的平均值
    smoothed_value = sum(adc_readings) / len(adc_readings)
    
    return smoothed_value

# --- 3. 主程式迴圈 ---

print("實驗 #5-2 開始：調整LED閃爍速度...")
print("轉動可變電阻來改變亮滅時間。")

try:
    while True:
        # 步驟 1: 取得平滑處理後的 ADC 值
        smoothed_adc_value = get_smoothed_adc()
        
        # 步驟 2: 將平滑後的 ADC 值映射到指定的亮滅時間範圍
        # 限制 ADC 值在設定的範圍內，避免極端情況
        clamped_adc = max(ADC_MIN, min(smoothed_adc_value, ADC_MAX))
        delay_time = map_value(clamped_adc, ADC_MIN, ADC_MAX, TIME_MIN, TIME_MAX)
        
        # 步驟 3: 將計算出的亮滅時間列印到互動環境
        # 使用 f-string 格式化輸出，保留兩位小數
        print(f"ADC平滑值: {smoothed_adc_value:.0f}, 對應亮滅時間: {delay_time:.2f} 秒")
        
        # 步驟 4: 控制 LED 亮滅
        # 讓所有 LED 亮起
        for led in leds:
            led.on()
        
        # 等待計算出的時間
        time.sleep(delay_time)
        
        # 讓所有 LED 熄滅
        for led in leds:
            led.off()
        
        # 再次等待計算出的時間，完成一個完整的閃爍週期
        time.sleep(delay_time)
        
except KeyboardInterrupt:
    # 當在 Thonny 按下 Ctrl+C 時，會觸發 KeyboardInterrupt
    print("程式已停止。")
    # 確保程式結束時所有 LED 都是熄滅的
    for led in leds:
        led.off()