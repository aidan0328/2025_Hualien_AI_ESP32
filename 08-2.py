# 實驗 #8-2：WS2812B 單顆燈順時針旋轉 + 按鈕切換彩虹顏色
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import neopixel
import time

# --- 硬體腳位定義 ---
PIN_NEOPIXEL = 4      # WS2812B LED 燈環的訊號腳位
PIN_BUTTON = 23       # 按鈕腳位
PIN_POTENTIOMETER = 36 # 可變電阻腳位 (ADC1_CH0)

# --- LED 燈環設定 ---
NUM_LEDS = 12         # LED 數量

# --- 顏色定義 (紅、橙、黃、綠、藍、靛、紫) ---
RAINBOW_COLORS = (
    (255, 0, 0),      # 紅色
    (255, 127, 0),    # 橙色
    (255, 255, 0),    # 黃色
    (0, 255, 0),      # 綠色
    (0, 0, 255),      # 藍色
    (75, 0, 130),     # 靛色 (Indigo)
    (148, 0, 211)     # 紫色 (Violet)
)

# --- 初始化硬體 ---

# 1. 初始化 NeoPixel LED 燈環
#    - machine.Pin(PIN_NEOPIXEL) : 設定 GPIO4 為輸出
#    - neopixel.NeoPixel(...) : 建立 NeoPixel 物件
np = neopixel.NeoPixel(machine.Pin(PIN_NEOPIXEL), NUM_LEDS)

# 2. 初始化按鈕
#    - machine.Pin.IN : 設定為輸入模式
#    - machine.Pin.PULL_DOWN : 啟用內部下拉電阻，確保未按下時為穩定的低電位
button = machine.Pin(PIN_BUTTON, machine.Pin.IN, machine.Pin.PULL_DOWN)

# 3. 初始化可變電阻 (ADC)
#    - machine.ADC(...) : 建立 ADC 物件
#    - adc.atten(machine.ADC.ATTN_11DB) : 設定衰減，使 ADC 可以讀取完整的 0V ~ 3.3V 電壓範圍
adc = machine.ADC(machine.Pin(PIN_POTENTIOMETER))
adc.atten(machine.ADC.ATTN_11DB)

# --- 狀態變數 ---
current_led_index = 0      # 當前點亮的 LED 索引 (0-11)
current_color_index = 0    # 當前使用的顏色索引 (0-6)
last_move_time = 0         # 上次 LED 移動的時間戳 (毫秒)
last_button_state = 0      # 上次讀取的按鈕狀態 (用於邊緣檢測)

print("實驗 #8-2 程式已啟動。")
print("旋轉可變電阻可調整速度，按下按鈕可切換顏色。")

# --- 主迴圈 ---
while True:
    # --- 1. 處理按鈕輸入 (切換顏色) ---
    current_button_state = button.value()
    # 檢查按鈕是否被「按下」(從 0 變成 1)，而不是「按住」
    if current_button_state == 1 and last_button_state == 0:
        # 切換到下一個顏色
        current_color_index = (current_color_index + 1) % len(RAINBOW_COLORS)
        print(f"顏色已切換，當前顏色索引: {current_color_index}")
        # 為了避免按太快，可以加入一個小的延遲，但此處省略以符合非阻塞要求
        # 更好的做法是使用 debounce 計時器，但邊緣檢測已能應付多數情況
        
    last_button_state = current_button_state # 更新按鈕狀態

    # --- 2. 處理可變電阻輸入 (調整速度) ---
    # ESP32 的 ADC 是 12-bit，讀取值範圍 0-4095
    pot_value = adc.read()
    
    # 將 ADC 讀值 (0-4095) 映射到一個合理的延遲時間 (例如 50ms 到 500ms)
    # 逆時針到底 (0V, pot_value=0) -> 最慢 (500ms)
    # 順時針到底 (3.3V, pot_value=4095) -> 最快 (50ms)
    # 公式: min_delay + (1 - (value / max_value)) * (max_delay - min_delay)
    # 這裡用簡化公式: 500 - (pot_value / 4095) * 450
    rotation_delay_ms = 500 - (pot_value / 4095) * 450
    
    # --- 3. 處理 LED 動畫 (非阻塞式旋轉) ---
    current_time = time.ticks_ms() # 獲取當前時間
    
    # 檢查距離上次移動是否已超過指定的延遲時間
    if time.ticks_diff(current_time, last_move_time) >= rotation_delay_ms:
        last_move_time = current_time # 更新移動時間戳
        
        # a. 先將所有 LED 熄滅
        np.fill((0, 0, 0))
        
        # b. 取得當前要顯示的顏色
        active_color = RAINBOW_COLORS[current_color_index]
        
        # c. 點亮指定的 LED
        np[current_led_index] = active_color
        
        # d. 將更新後的顏色資料寫入 LED 燈環
        np.write()
        
        # e. 計算下一個要點亮的 LED 索引 (0 -> 1 -> ... -> 11 -> 0)
        current_led_index = (current_led_index + 1) % NUM_LEDS