# 實驗 #9-1： 按鈕切換顏色 + 可變電阻控制亮度 + 超音波感測器調整旋轉速度
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import neopixel
import time
from machine import Pin, ADC

# --- 硬體腳位定義 ---
NEOPIXEL_PIN = 4
POT_PIN = 36         # 可變電阻
BUTTON_PIN = 23      # 按鈕
ULTRASONIC_TRIG_PIN = 27 # 超音波 Trig
ULTRASONIC_ECHO_PIN = 13 # 超音波 Echo

# --- LED 燈條設定 ---
NUM_LEDS = 12

# --- 顏色定義 (RGB) ---
# 🔴紅 -> 🧡橙 -> 🟡黃 -> 🟢綠 -> 🔵藍 -> 🟣靛 -> 🟪紫
COLORS = [
    (255, 0, 0),    # 紅
    (255, 127, 0),  # 橙
    (255, 255, 0),  # 黃
    (0, 255, 0),    # 綠
    (0, 0, 255),    # 藍
    (75, 0, 130),   # 靛 (Indigo)
    (148, 0, 211)   # 紫 (Violet)
]

# --- 硬體初始化 ---
# WS2812B LED 燈環
np = neopixel.NeoPixel(Pin(NEOPIXEL_PIN, Pin.OUT), NUM_LEDS)

# 可變電阻 (ADC)
# ATTN_11DB 允許 ADC 讀取完整的 0-3.3V 範圍
pot = ADC(Pin(POT_PIN))
pot.atten(ADC.ATTN_11DB)

# 按鈕 (輸入)
# 按下為高電位，所以我們使用 PULL_DOWN 使其在未按下時保持穩定低電位
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)

# 超音波模組
trig = Pin(ULTRASONIC_TRIG_PIN, Pin.OUT)
echo = Pin(ULTRASONIC_ECHO_PIN, Pin.IN)


# --- 輔助函式 ---

def get_distance_cm():
    """
    觸發 HC-SR04 並回傳測量到的距離（公分）。
    如果超時，則回傳一個較大的值（例如 51），讓速度變為最慢。
    """
    # 發送觸發信號
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    try:
        # 測量回波信號的脈衝持續時間 (us)
        # timeout 設為 30000us (30ms)，對應約 5 公尺的距離，避免永久等待
        pulse_duration = machine.time_pulse_us(echo, 1, 30000)
        # 距離(cm) = (脈衝時間 * 音速) / 2
        # 音速約 343 m/s 或 0.0343 cm/us
        # 距離 = (pulse_duration * 0.0343) / 2 = pulse_duration / 58.3
        distance = pulse_duration / 58.3
        return distance
    except OSError:
        # 若 time_pulse_us 超時，會引發 OSError
        return 51.0  # 回傳一個大於 50 的值，使速度為最慢

def map_value(x, in_min, in_max, out_min, out_max):
    """
    將一個數值從一個範圍線性映射到另一個範圍。
    """
    # 先限制輸入值在輸入範圍內，避免超出預期
    x = max(in_min, min(x, in_max))
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

# --- 狀態變數初始化 ---
current_led_index = 0
current_color_index = 0
last_button_state = 0  # 用於按鈕的邊緣檢測

# 非阻塞式計時器
last_led_update_time = time.ticks_ms()
last_print_time = time.ticks_ms()

print("實驗 #9-1 已啟動。")
print("按按鈕切換顏色，轉動可變電阻調整亮度，用手靠近超音波感測器改變速度。")

# --- 主迴圈 ---
while True:
    # 獲取當前時間，用於所有非阻塞式計時
    now = time.ticks_ms()

    # 1. 處理按鈕輸入 (顏色切換)
    button_state = button.value()
    # 邊緣檢測：僅在按鈕從「未按下」(0) 變為「按下」(1) 時觸發
    if button_state == 1 and last_button_state == 0:
        current_color_index = (current_color_index + 1) % len(COLORS)
        print(f"按鈕按下！切換顏色至: {current_color_index}")
        # 簡單的軟體去抖動
        time.sleep_ms(20) 
    last_button_state = button_state

    # 2. 讀取感測器數值
    pot_value = pot.read()        # 讀取可變電阻 (0-4095)
    distance_cm = get_distance_cm() # 讀取超音波距離

    # 3. 計算參數
    # 將電阻值 (0-4095) 映射到亮度 (0-255)
    brightness = map_value(pot_value, 0, 4095, 0, 255)
    
    # 將距離 (5-50 cm) 映射到旋轉時間 (0.5-2 秒/圈)
    # 總旋轉時間 (ms) = 500ms (最快) 到 2000ms (最慢)
    total_rotation_time_ms = map_value(int(distance_cm), 5, 50, 500, 2000)
    
    # 每顆 LED 的亮燈間隔時間
    rotation_interval_ms = total_rotation_time_ms // NUM_LEDS
    
    # 4. 定期列印距離資訊 (避免洗版)
    if time.ticks_diff(now, last_print_time) > 500: # 每 500ms 列印一次
        print(f"偵測距離: {distance_cm:.1f} cm, 亮度: {brightness}, 旋轉間隔: {rotation_interval_ms} ms")
        last_print_time = now

    # 5. 更新 LED 狀態 (非阻塞式)
    if time.ticks_diff(now, last_led_update_time) >= rotation_interval_ms:
        last_led_update_time = now
        
        # 獲取當前基礎顏色
        base_color = COLORS[current_color_index]
        
        # 根據亮度調整顏色
        # new_color = base_color * (brightness / 255)
        bright_color = (
            (base_color[0] * brightness) // 255,
            (base_color[1] * brightness) // 255,
            (base_color[2] * brightness) // 255
        )
        
        # 更新燈環：先全部熄滅，再點亮指定的一顆
        np.fill((0, 0, 0))
        
        # 只有在亮度不為0時才點亮燈
        if brightness > 0:
            np[current_led_index] = bright_color
        
        # 將更新後的顏色數據寫入燈環
        np.write()
        
        # 移動到下一顆 LED，準備下次更新
        current_led_index = (current_led_index + 1) % NUM_LEDS