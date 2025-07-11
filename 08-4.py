# 實驗 #8-4：單顆彩虹燈順時針旋轉 + 按鈕切換顏色 + 可變電阻調整亮度/速度
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import neopixel
import time

# --- 硬體接腳定義 ---
LED_PIN = 4         # WS2812B LED 燈環的訊號腳
VR_PIN = 36         # 可變電阻 (ADC1_CH0)
BUTTON_PIN = 23     # 按鈕

# --- LED 燈環設定 ---
NUM_LEDS = 12       # 燈珠數量

# --- 功能參數設定 ---
LONG_PRESS_MS = 1000  # 長按定義：1000 毫秒 (1秒)

# 彩虹顏色順序 (R, G, B)
COLORS = [
    (255, 0, 0),    # 🔴 紅
    (255, 127, 0),  # 🧡 橙
    (255, 255, 0),  # 🟡 黃
    (0, 255, 0),    # 🟢 綠
    (0, 0, 255),    # 🔵 藍
    (75, 0, 130),   # 🟣 靛 (Indigo)
    (148, 0, 211)   # 🟪 紫 (Violet)
]

# 可變電阻 ADC 讀取範圍 (ESP32 預設為 12-bit)
VR_MIN = 0
VR_MAX = 4095

# 速度模式下的旋轉週期範圍 (毫秒)
SPEED_MIN_MS = 50   # 0.05 秒
SPEED_MAX_MS = 1000 # 1 秒

# 亮度模式下的亮度範圍
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 1.0 # 使用 0.0 到 1.0 的浮點數比例，方便計算

# --- 硬體初始化 ---
# 初始化 NeoPixel 燈環
np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)

# 初始化可變電阻的 ADC
# set_atten(ADC.ATTN_11DB) 可讓 ADC 讀取完整的 0-3.3V 範圍
adc = machine.ADC(machine.Pin(VR_PIN))
adc.atten(machine.ADC.ATTN_11DB)

# 初始化按鈕，使用內建下拉電阻，按下時為高電位
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# --- 狀態變數 ---
# 動畫狀態
current_led_index = 0
last_led_update_time = 0

# 顏色狀態
current_color_index = 0

# 按鈕狀態
button_press_time = 0
last_button_state = 0

# 模式狀態 ('BRIGHTNESS' 或 'SPEED')
mode = 'BRIGHTNESS'

# 可變參數狀態
brightness = BRIGHTNESS_MAX  # 初始亮度為最亮
speed_period_ms = 200        # 初始速度 (毫秒)

# --- 輔助函式 ---
def map_value(x, in_min, in_max, out_min, out_max):
    """將一個值從一個範圍線性映射到另一個範圍"""
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def apply_brightness(color, brightness_level):
    """將亮度應用到顏色上"""
    # 確保亮度在 0.0 到 1.0 之間
    brightness_level = max(0.0, min(1.0, brightness_level))
    # 將 RGB 的每個分量乘以亮度比例
    return tuple(int(c * brightness_level) for c in color)

# --- 主程式迴圈 ---
print("程式啟動！初始模式：亮度調整")
print("短按按鈕切換顏色，長按按鈕切換模式。")

while True:
    # 取得當前時間戳，用於所有非阻塞式計時
    now = time.ticks_ms()

    # 1. 處理按鈕邏輯 (短按/長按)
    # ------------------------------------
    current_button_state = button.value()
    
    # 偵測到按鈕被按下 (從 0 -> 1)
    if current_button_state == 1 and last_button_state == 0:
        button_press_time = now
    
    # 偵測到按鈕被放開 (從 1 -> 0)
    elif current_button_state == 0 and last_button_state == 1:
        press_duration = time.ticks_diff(now, button_press_time)
        
        if press_duration >= LONG_PRESS_MS:
            # --- 長按：切換模式 ---
            if mode == 'BRIGHTNESS':
                mode = 'SPEED'
                print("模式切換 -> 速度調整 (VR: 0.05秒 - 1秒)")
            else:
                mode = 'BRIGHTNESS'
                print("模式切換 -> 亮度調整 (VR: 熄滅 - 最亮)")
        else:
            # --- 短按：切換顏色 ---
            current_color_index = (current_color_index + 1) % len(COLORS)
            color_names = ["紅", "橙", "黃", "綠", "藍", "靛", "紫"]
            print(f"顏色切換 -> {color_names[current_color_index]}")

    last_button_state = current_button_state

    # 2. 處理可變電阻邏輯
    # ------------------------------------
    vr_value = adc.read()
    
    if mode == 'BRIGHTNESS':
        # 亮度模式：VR 控制亮度
        # 將 ADC 讀值 (0-4095) 映射到亮度比例 (0.0-1.0)
        brightness = map_value(vr_value, VR_MIN, VR_MAX, BRIGHTNESS_MIN, BRIGHTNESS_MAX)
    else: # mode == 'SPEED'
        # 速度模式：VR 控制速度
        # 將 ADC 讀值 (0-4095) 映射到旋轉週期 (50ms-1000ms)
        speed_period_ms = map_value(vr_value, VR_MIN, VR_MAX, SPEED_MIN_MS, SPEED_MAX_MS)

    # 3. 處理 LED 動畫邏輯
    # ------------------------------------
    # 檢查是否到達下一次更新 LED 的時間
    if time.ticks_diff(now, last_led_update_time) >= speed_period_ms:
        last_led_update_time = now  # 重置計時器

        # a. 先將所有燈珠熄滅
        np.fill((0, 0, 0))

        # b. 計算目前應顯示的顏色 (基底顏色 + 亮度調整)
        base_color = COLORS[current_color_index]
        final_color = apply_brightness(base_color, brightness)

        # c. 點亮當前的燈珠
        # 如果亮度為 0，final_color 會是 (0,0,0)，燈珠自然熄滅
        np[current_led_index] = final_color

        # d. 更新燈環顯示
        np.write()

        # e. 將索引指向下一個燈珠，準備下一次點亮
        current_led_index = (current_led_index + 1) % NUM_LEDS