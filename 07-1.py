# ----------------------------------------------------------------------
# 實驗 #7-1：WS2812B 的基本驅動
#
# 說明：
# 本程式碼使用非阻塞式 (non-blocking) 的方式驅動兩顆串接的 WS2812B LED，
# 讓它們同步顯示彩虹顏色的變化效果。
#
# 執行環境：
# - MicroPython v1.24.0
# - ESP32-DevKitC
#
# 硬體接線：
# - 兩顆 WS2812B LED 串接
# - Data In (DI) 接至 ESP32 的 GPIO2
# - VCC 接至 5V
# - GND 接至 GND
# ----------------------------------------------------------------------

import machine
import neopixel
import time

# --- 硬體與參數設定 ---

# WS2812B LED 的 GPIO 接腳
PIN_NUM = 2
# LED 燈珠的數量
NUM_LEDS = 2
# 每個顏色持續的時間 (毫秒)
COLOR_INTERVAL_MS = 1000

# --- 初始化硬體 ---

# 設定 GPIO2 為輸出模式
pin = machine.Pin(PIN_NUM, machine.Pin.OUT)
# 初始化 NeoPixel 物件
# 參數：(腳位物件, LED數量)
np = neopixel.NeoPixel(pin, NUM_LEDS)

# --- 定義顏色 ---
# 定義彩虹變化的顏色順序，每個顏色為一個 (R, G, B) 元組
RAINBOW_COLORS = [
    (0, 0, 0),       # 0: OFF (關閉)
    (255, 0, 0),     # 1: 紅 (Red)
    (255, 127, 0),   # 2: 橙 (Orange)
    (255, 255, 0),   # 3: 黃 (Yellow)
    (0, 255, 0),     # 4: 綠 (Green)
    (0, 0, 255),     # 5: 藍 (Blue)
    (75, 0, 130),    # 6: 靛 (Indigo)
    (148, 0, 211)    # 7: 紫 (Violet)
]

# --- 狀態變數 ---

# 當前顯示的顏色在 RAINBOW_COLORS 列表中的索引
current_color_index = 0
# 上次更新顏色的時間戳 (使用 ticks_ms)
last_update_time = time.ticks_ms()

# --- 主程式 ---

print("實驗 #7-1：WS2812B 非阻塞式彩虹燈效果啟動...")
print(f"硬體: {NUM_LEDS} 顆 LED 燈珠接在 GPIO{PIN_NUM}")
print(f"設定: 每種顏色持續 {COLOR_INTERVAL_MS / 1000} 秒")

# 初始狀態：將所有 LED 設定為第一個顏色 (OFF)
np.fill(RAINBOW_COLORS[current_color_index])
np.write()
print(f"初始顏色: OFF {RAINBOW_COLORS[current_color_index]}")

try:
    # 進入主迴圈，程式會永遠在這裡運行
    while True:
        # 獲取當前時間
        current_time = time.ticks_ms()

        # 檢查距離上次更新是否已超過指定間隔
        # time.ticks_diff() 用於正確處理計時器溢位問題
        if time.ticks_diff(current_time, last_update_time) >= COLOR_INTERVAL_MS:
            
            # 1. 更新時間戳
            last_update_time = current_time

            # 2. 計算下一個顏色的索引
            # 使用取餘數 (%) 運算子來實現循環效果
            current_color_index = (current_color_index + 1) % len(RAINBOW_COLORS)

            # 3. 獲取新的顏色值
            new_color = RAINBOW_COLORS[current_color_index]

            # 4. 更新所有 LED 的顏色
            # np.fill() 會將所有燈珠設定為相同的顏色
            np.fill(new_color)
            
            # 5. 將顏色資料寫入 LED，使其生效
            np.write()
            
            # 在終端機印出當前狀態，方便除錯與觀察
            print(f"時間: {current_time/1000:.2f}s, 顏色索引: {current_color_index}, RGB: {new_color}")

        # 在此處可以加入其他非阻塞的程式碼，例如讀取感測器、檢查網路等
        # 由於主迴圈沒有 sleep()，反應會非常及時
        
except KeyboardInterrupt:
    print("程式被使用者中斷...")

finally:
    # 程式結束或中斷時，確保關閉所有 LED，避免殘留亮光
    print("清理資源，關閉所有 LED。")
    np.fill((0, 0, 0))
    np.write()