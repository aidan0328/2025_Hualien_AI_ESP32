# 實驗 #8-3：單顆彩虹燈順時針旋轉 + 按鈕切換顏色 + 可變電阻調整亮度
# 執行環境：MicroPython v1.24.0, ESP32-DevKitC

import machine
import neopixel
import time

# --- 硬體腳位與常數設定 ---
# WS2812B LED 燈環
LED_PIN = 4
NUM_LEDS = 12

# 按鈕 (按下為高電位)
BUTTON_PIN = 23

# 可變電阻 (ADC)
POT_PIN = 36

# --- 動畫與狀態變數 ---
# 動畫更新間隔 (毫秒)
# 數值越小，旋轉越快
MOVE_INTERVAL_MS = 100 
last_move_time = 0  # 上次移動 LED 的時間戳

# 目前點亮的 LED 索引
led_index = 0

# 彩虹顏色列表 (R, G, B)
COLORS = (
    (255, 0, 0),      # 🔴 紅色
    (255, 127, 0),    # 🧡 橙色
    (255, 255, 0),    # 🟡 黃色
    (0, 255, 0),      # 🟢 綠色
    (0, 0, 255),      # 🔵 藍色
    (75, 0, 130),     # 🟣 靛色
    (148, 0, 211)     # 🟪 紫色
)
color_index = 0 # 目前顏色索引

# 按鈕狀態，用於偵測邊緣觸發 (防止重複觸發)
last_button_state = 0

# --- 硬體初始化 ---
# 1. 初始化 NeoPixel 燈條
#    使用 machine.Pin(LED_PIN) 來指定腳位
np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)

# 2. 初始化按鈕
#    machine.Pin.IN 表示這是一個輸入腳位
button = machine.Pin(BUTTON_PIN, machine.Pin.IN)

# 3. 初始化 ADC (類比數位轉換器) for 可變電阻
#    ESP32 的 ADC 腳位範圍為 0-3.3V
adc = machine.ADC(machine.Pin(POT_PIN))
#    設定衰減，以讀取完整的 0-3.3V 範圍
adc.atten(machine.ADC.ATTN_11DB)
#    設定 ADC 解析度為 12-bit (0-4095)
adc.width(machine.ADC.WIDTH_12BIT)


print("實驗 #8-3 啟動：互動式彩虹燈")
print("硬體接線：")
print(f"  - WS2812B (12燈): GPIO{LED_PIN}")
print(f"  - 可變電阻: GPIO{POT_PIN}")
print(f"  - 按鈕: GPIO{BUTTON_PIN}")
print("程式執行中...")


# --- 主迴圈 ---
try:
    while True:
        # 獲取當前時間，用於非阻塞式延遲
        current_time = time.ticks_ms()

        # 1. 讀取可變電阻並計算亮度
        #    adc.read() 會回傳 0 (0V) 到 4095 (3.3V) 之間的數值
        pot_value = adc.read()
        #    將 0-4095 的讀值線性對應到 0.0-1.0 的亮度比例
        brightness = pot_value / 4095.0

        # 2. 偵測按鈕狀態並切換顏色
        current_button_state = button.value()
        #    判斷是否為「按下」的瞬間 (從 0 變為 1)
        if current_button_state == 1 and last_button_state == 0:
            color_index = (color_index + 1) % len(COLORS)
            print(f"按鈕觸發！切換顏色至索引 {color_index}")
            # 短暫延遲以避免機械彈跳 (debounce)
            time.sleep_ms(20) 
        #    更新按鈕狀態
        last_button_state = current_button_state
        
        # 3. 處理 LED 旋轉動畫 (非阻塞式)
        #    使用 time.ticks_diff 檢查是否已達到指定的更新間隔
        if time.ticks_diff(current_time, last_move_time) >= MOVE_INTERVAL_MS:
            # 更新時間戳
            last_move_time = current_time

            # 計算下一個要點亮的 LED 索引 (順時針)
            led_index = (led_index + 1) % NUM_LEDS
            
            # --- 更新燈光顯示 ---
            # a. 取得目前的基礎顏色
            base_color = COLORS[color_index]
            
            # b. 根據可變電阻的亮度調整顏色
            #    將 R, G, B 各分量乘以亮度比例，並轉換為整數
            bright_color = (
                int(base_color[0] * brightness),
                int(base_color[1] * brightness),
                int(base_color[2] * brightness)
            )

            # c. 將所有 LED 燈先熄滅 (填滿黑色)
            np.fill((0, 0, 0))
            
            # d. 只點亮當前索引的 LED
            np[led_index] = bright_color
            
            # e. 將更新後的顏色資料寫入燈條
            np.write()

# 使用 try...finally 確保程式被中斷時 (例如按下 Ctrl+C)，能將所有LED關閉
finally:
    np.fill((0, 0, 0))
    np.write()
    print("程式已停止，所有 LED 已關閉。")