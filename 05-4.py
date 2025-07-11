# 實驗 #5-4：使用可變電阻調整跑馬燈速度
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import time

# --- 硬體腳位定義 ---
# 可變電阻連接到 ADC1 的 CH0 (GPIO36)
pot_pin = machine.ADC(machine.Pin(36))
# 設定 ADC 的衰減，使其可以測量 0-3.3V 的電壓
# ATTN_11DB 對應最大輸入電壓約 3.3V，輸出範圍 0-4095
pot_pin.atten(machine.ADC.ATTN_11DB)

# LED 模組腳位 (紅, 黃, 綠)
led_pins_numbers = [18, 19, 21]
leds = [machine.Pin(pin, machine.Pin.OUT) for pin in led_pins_numbers]

# --- 參數設定 ---
# ADC 讀值範圍
ADC_MIN = 0
ADC_MAX = 4095  # 12-bit ADC

# 跑馬燈一輪總時間範圍 (秒)
TIME_MIN_S = 0.5
TIME_MAX_S = 10.0

# 跑馬燈的路徑為 R -> Y -> G -> Y -> R ... 共 4 個步驟
NUM_STEPS = 4

# 移動平均的樣本數
MOVING_AVG_SAMPLES = 10

# --- 輔助函式 ---
def map_value(x, in_min, in_max, out_min, out_max):
    """將一個值從一個範圍線性映射到另一個範圍"""
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def all_leds_off():
    """關閉所有 LED"""
    for led in leds:
        led.value(0)

# --- 主程式 ---
print("實驗 #5-4：可變電阻調整跑馬燈速度")
print("逆時針轉到底最快 (0.5秒/輪)，順時針轉到底最慢 (10秒/輪)")

# --- 狀態變數初始化 ---
# 初始化 ADC 移動平均列表，全部填入 0
adc_readings = [0] * MOVING_AVG_SAMPLES

# 跑馬燈順序：0=紅, 1=黃, 2=綠。來回模式為 [紅, 黃, 綠, 黃]
led_sequence_indices = [0, 1, 2, 1]
current_sequence_index = 0

# 用於非阻塞式延遲的時間戳
last_update_time = time.ticks_ms()

# 程式開始時，先點亮第一顆燈
all_leds_off()
leds[led_sequence_indices[current_sequence_index]].value(1)

try:
    while True:
        # 1. 讀取 ADC 並進行移動平均平滑處理
        # ------------------------------------
        raw_adc = pot_pin.read()
        
        # 移除最舊的讀值
        adc_readings.pop(0)
        # 加入最新的讀值
        adc_readings.append(raw_adc)
        
        # 計算平滑後的值
        smoothed_adc_value = sum(adc_readings) / MOVING_AVG_SAMPLES

        # 2. 將平滑後的 ADC 值映射到延遲時間
        # ------------------------------------
        # 計算跑馬燈一輪所需的總時間 (秒)
        total_cycle_time_s = map_value(smoothed_adc_value, ADC_MIN, ADC_MAX, TIME_MIN_S, TIME_MAX_S)
        
        # 計算每一步驟之間的延遲時間 (毫秒)
        delay_per_step_ms = (total_cycle_time_s / NUM_STEPS) * 1000

        # 3. 非阻塞式檢查是否到達切換時間
        # ------------------------------------
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_update_time) >= delay_per_step_ms:
            # 時間到了，更新 LED 狀態
            
            # 將目前的燈熄滅
            leds[led_sequence_indices[current_sequence_index]].value(0)
            
            # 計算下一個燈的索引
            current_sequence_index = (current_sequence_index + 1) % NUM_STEPS
            
            # 點亮下一個燈
            leds[led_sequence_indices[current_sequence_index]].value(1)
            
            # 更新上次切換的時間戳
            last_update_time = current_time

        # 可以在這裡加入一個極短的延遲，避免 CPU 佔用率 100%
        # 但對於這個應用不是必需的，因為 ADC 讀取本身就有延遲
        # time.sleep_ms(1) 

except KeyboardInterrupt:
    print("程式被使用者中斷")

finally:
    # 確保程式結束時所有 LED 都會熄滅
    print("清理 GPIO...")
    all_leds_off()
    print("程式結束")