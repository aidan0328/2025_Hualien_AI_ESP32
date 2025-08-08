# 實驗 #8-2：WS2812B 單顆燈順時針旋轉 + 按鈕切換彩虹顏色
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import neopixel
import time

# --- 硬體和常數定義 ---

# WS2812B LED 燈環設定
NUM_LEDS = 12
PIN_NEOPIXEL = 4

# 按鈕設定
PIN_BUTTON = 23

# 動畫和功能設定
ROTATION_INTERVAL_MS = 80  # LED 旋轉速度（毫秒），數值越小轉越快
DEBOUNCE_DELAY_MS = 50   # 按鈕去抖動延遲（毫秒）

# 彩虹顏色定義 (R, G, B)
COLORS = (
    (255, 0, 0),    # 0: 紅色
    (255, 127, 0),  # 1: 橙色
    (255, 255, 0),  # 2: 黃色
    (0, 255, 0),    # 3: 綠色
    (0, 0, 255),    # 4: 藍色
    (75, 0, 130),   # 5: 靛色
    (148, 0, 211)   # 6: 紫色
)
COLOR_NAMES = ("紅色", "橙色", "黃色", "綠色", "藍色", "靛色", "紫色")

# --- 硬體初始化 ---

# 初始化 NeoPixel 燈條
# machine.Pin(PIN_NEOPIXEL) 創建 GPIO 物件
# neopixel.NeoPixel() 創建燈條控制物件
np = neopixel.NeoPixel(machine.Pin(PIN_NEOPIXEL), NUM_LEDS)

# 初始化按鈕
# machine.Pin.IN: 設定為輸入模式
# machine.Pin.PULL_DOWN: 啟用內部下拉電阻，當按鈕未按下時，腳位會被穩定在低電位
button = machine.Pin(PIN_BUTTON, machine.Pin.IN, machine.Pin.PULL_DOWN)

# --- 狀態變數 ---

# LED 旋轉相關狀態
current_led_index = 0
last_move_time = 0

# 顏色切換相關狀態
current_color_index = 0

# 按鈕去抖動相關狀態
button_state = 0          # 當前穩定的按鈕狀態 (0=放開, 1=按下)
last_button_state = 0     # 上一次讀取到的按鈕狀態 (用於偵測變化)
last_debounce_time = 0    # 上次按鈕狀態發生變化的時間點

# --- 主程式 ---

print("實驗 #8-2 啟動...")
print("單顆燈將開始順時針旋轉。")
print("按下按鈕可切換彩虹顏色。")
print("目前顏色: ", COLOR_NAMES[current_color_index])

try:
    while True:
        # 獲取當前時間，用於所有非阻塞式計時
        now = time.ticks_ms()

        # --- 任務1: 處理 LED 順時針旋轉 (非阻塞式) ---
        # 檢查是否已達到旋轉的時間間隔
        if time.ticks_diff(now, last_move_time) > ROTATION_INTERVAL_MS:
            last_move_time = now  # 重置計時器

            # 1. 將所有 LED 燈熄滅
            np.fill((0, 0, 0))

            # 2. 計算下一個要亮燈的索引 (0-11)，使用 % 運算子實現循環
            current_led_index = (current_led_index + 1) % NUM_LEDS

            # 3. 獲取當前選擇的顏色
            current_color = COLORS[current_color_index]

            # 4. 點亮指定索引的 LED
            np[current_led_index] = current_color
            
            # 5. 將顏色資料寫入燈條使其生效
            np.write()

        # --- 任務2: 處理按鈕按下事件 (非阻塞式 + 去抖動) ---
        reading = button.value()

        # 如果讀取到的狀態與上次不同（可能發生抖動或真實按壓），重置去抖動計時器
        if reading != last_button_state:
            last_debounce_time = now

        # 檢查按鈕狀態是否已穩定超過去抖動延遲時間
        if time.ticks_diff(now, last_debounce_time) > DEBOUNCE_DELAY_MS:
            # 如果穩定後的新狀態與之前記錄的穩定狀態不同
            if reading != button_state:
                button_state = reading  # 更新穩定的按鈕狀態
                
                # 如果新的穩定狀態是 "按下" (高電位)
                if button_state == 1:
                    # 這是一次有效的按壓事件
                    # 切換到下一個顏色，使用 % 運算子實現循環
                    current_color_index = (current_color_index + 1) % len(COLORS)
                    print("顏色切換: ", COLOR_NAMES[current_color_index])
        
        # 更新上次讀取的狀態，為下一次循環做準備
        last_button_state = reading

except KeyboardInterrupt:
    print("程式被使用者中斷")

finally:
    # 程式結束時，確保所有 LED 都被關閉
    np.fill((0, 0, 0))
    np.write()
    print("程式結束，所有LED已關閉。")
