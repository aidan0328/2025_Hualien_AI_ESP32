# 實驗 #7-2：WS2812B 漸進彩虹效果顯示
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC
# 硬體：2x WS2812B on GPIO2

import machine
import neopixel
import utime

# --- 參數設定 ---

# 硬體接線設定
PIN_NUM = 2          # WS2812B 的訊號線連接到 GPIO2
NUM_LEDS = 2         # LED 燈珠的數量

# 動畫效果設定
# 整個顏色循環的總時間 (毫秒)
CYCLE_DURATION_MS = 20 * 1000  # 20 秒

# --- 顏色定義 ---
# 定義彩虹的關鍵顏色幀 (Keyframes)
# 為了實現從紅色平滑過渡回紅色，我們在列表末尾再次加入紅色
# 順序：紅 -> 橙 -> 黃 -> 綠 -> 藍 -> 靛 -> 紫 -> 紅
RAINBOW_KEYFRAMES = [
    (255, 0, 0),    # 1. 紅 (Red)
    (255, 127, 0),  # 2. 橙 (Orange)
    (255, 255, 0),  # 3. 黃 (Yellow)
    (0, 255, 0),    # 4. 綠 (Green)
    (0, 0, 255),    # 5. 藍 (Blue)
    (75, 0, 130),   # 6. 靛 (Indigo)
    (148, 0, 211),  # 7. 紫 (Violet)
    (255, 0, 0)     # 8. 回到 紅 (Red) 以形成閉環
]

# --- 硬體初始化 ---
# 設定 GPIO2 為輸出模式
pin = machine.Pin(PIN_NUM, machine.Pin.OUT)
# 初始化 NeoPixel 物件
# 參數: (腳位物件, LED數量)
np = neopixel.NeoPixel(pin, NUM_LEDS)

# --- 主程式 ---
print("實驗 #7-2：WS2812B 漸進彩虹效果顯示")
print(f"硬體: {NUM_LEDS} 顆 LED燈珠於 GPIO{PIN_NUM}")
print(f"效果: 20秒平滑彩虹循環 (非阻塞式)")

# 記錄主迴圈開始的時間點，作為計算基準
start_time = utime.ticks_ms()

# 主迴圈，程式會在這裡不斷運行
while True:
    # 1. 計算當前在20秒循環中的位置 (非阻塞式計時)
    # --------------------------------------------------
    # utime.ticks_ms() 獲取系統運行時間(毫秒)
    # utime.ticks_diff() 計算時間差，能處理計時器溢位問題
    # % CYCLE_DURATION_MS 確保時間永遠在 0 到 19999 之間循環
    current_time = utime.ticks_ms()
    time_in_cycle = utime.ticks_diff(current_time, start_time) % CYCLE_DURATION_MS

    # 2. 計算當前處於哪個顏色漸變的"區段"
    # --------------------------------------------------
    # 我們有8個顏色點，構成7個漸變區段 (紅->橙, 橙->黃, ...)
    num_segments = len(RAINBOW_KEYFRAMES) - 1
    # 計算每個區段應該持續多久
    segment_duration = CYCLE_DURATION_MS / num_segments
    # 根據當前時間，計算出我們在哪個區段 (0 到 6)
    segment_index = int(time_in_cycle / segment_duration)
    # 確保索引不會因為浮點數誤差而超出範圍
    segment_index = min(segment_index, num_segments - 1)

    # 3. 計算在當前區段內的進度
    # --------------------------------------------------
    # 獲取這個區段的起始顏色和結束顏色
    start_color = RAINBOW_KEYFRAMES[segment_index]
    end_color = RAINBOW_KEYFRAMES[segment_index + 1]
    
    # 計算時間在當前區段中已經經過了多少
    time_in_segment = time_in_cycle - (segment_index * segment_duration)
    # 將時間進度轉換為 0.0 到 1.0 之間的比例
    progress = time_in_segment / segment_duration

    # 4. 線性插值計算最終顏色
    # --------------------------------------------------
    # 這是實現平滑漸變的核心公式：
    # 當前值 = 起始值 * (1 - 進度) + 結束值 * 進度
    r = int(start_color[0] * (1 - progress) + end_color[0] * progress)
    g = int(start_color[1] * (1 - progress) + end_color[1] * progress)
    b = int(start_color[2] * (1 - progress) + end_color[2] * progress)
    
    current_color = (r, g, b)

    # 5. 更新 LED 顏色
    # --------------------------------------------------
    # 將計算出的顏色應用到所有 LED 上
    for i in range(NUM_LEDS):
        np[i] = current_color
        
    # 將顏色數據寫入到 WS2812B 燈條，使其顯示
    np.write()
    
    # 注意：這裡沒有使用 time.sleep() 或 utime.sleep()，
    # 迴圈會盡可能快地執行，不斷重新計算並更新顏色，
    # 使得顏色的變化完全由時間控制，達到最平滑的效果。