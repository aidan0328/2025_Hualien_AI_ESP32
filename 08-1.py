# 🧪 實驗 #8-1：WS2812B 單顆藍燈順時針旋轉動畫
# ----------------------------------------------------
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC
# ----------------------------------------------------

import machine
import neopixel
import time

# --- 硬體腳位與常數設定 ---
LED_PIN = 4          # WS2812B 連接的 GPIO
NUM_LEDS = 12        # WS2812B 燈環的 LED 數量
POT_PIN = 36         # 可變電阻連接的 GPIO (ADC1_CH0)
BUTTON_PIN = 23      # 按鈕連接的 GPIO

# --- 顏色定義 (R, G, B) ---
BLUE = (0, 0, 255)   # 藍色
OFF = (0, 0, 0)      # 熄滅

# --- 硬體初始化 ---

# 1. 初始化 WS2812B (NeoPixel) 燈環
#    neopixel.NeoPixel(腳位物件, LED數量)
np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)

# 2. 初始化可變電阻的 ADC (類比數位轉換器)
#    ESP32 的 ADC 腳位在 GPIO32-GPIO39 之間
pot = machine.ADC(machine.Pin(POT_PIN))
#    設定衰減，讓 ADC 可以讀取完整的 0V-3.3V 電壓範圍
pot.atten(machine.ADC.ATTN_11DB)
#    設定解析度為 12-bit，讀取值範圍為 0-4095
pot.width(machine.ADC.WIDTH_12BIT)

# 3. 初始化按鈕
#    設定為輸入模式，並啟用內部下拉電阻
#    這樣在按鈕未按下時，腳位會穩定在低電位(0)
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# --- 變數初始化 ---
current_led_index = 0  # 目前亮燈的索引，從第 0 顆開始
last_update_time = 0   # 上次更新燈光的時間戳記 (毫秒)

print("實驗 #8-1 啟動：單顆藍燈順時針旋轉")
print("轉動可變電阻可調整旋轉速度。")
print("按下 Ctrl+C 來停止程式。")

# 使用 try...finally 確保程式結束時能關閉所有LED
try:
    # --- 主迴圈 ---
    while True:
        # --- 1. 讀取輸入與計算 ---
        # 讀取可變電阻的值 (0-4095)
        pot_value = pot.read()

        # 將可變電阻的值映射到一個速度區間 (例如 50ms 到 500ms)
        # pot_value=0 (逆時針到底) -> 速度最快 (間隔最短)
        # pot_value=4095 -> 速度最慢 (間隔最長)
        # update_interval = 最小間隔 + (讀取比例 * 區間範圍)
        update_interval = 50 + int((pot_value / 4095) * 450)

        # 讀取按鈕狀態 (在此實驗中未使用，但已初始化)
        button_state = button.value()

        # --- 2. 非阻塞式延遲檢查 ---
        # 這是實現非阻塞動畫的核心
        current_time = time.ticks_ms() # 獲取當前時間 (毫秒)

        # 檢查從上次更新到現在，是否已經過了 update_interval 所設定的時間
        # time.ticks_diff() 用於安全地計算時間差，可避免計時器溢位問題
        if time.ticks_diff(current_time, last_update_time) >= update_interval:
            
            # --- 3. 更新 LED 動畫 ---
            last_update_time = current_time  # 更新最後更新時間

            # a. 將所有燈都熄滅
            np.fill(OFF)

            # b. 只點亮當前索引的燈
            np[current_led_index] = BLUE

            # c. 將顏色資料寫入燈環使其生效
            np.write()

            # d. 計算下一個要亮的燈的索引
            #    使用取餘數 (%) 運算子，確保索引值在 0 到 11 之間循環
            #    例如：(11 + 1) % 12 = 0，實現環狀效果
            current_led_index = (current_led_index + 1) % NUM_LEDS


# 當使用者按下 Ctrl+C 中斷程式時，會執行 finally 區塊
finally:
    # --- 清理作業 ---
    # 關閉所有LED燈，避免程式停止後燈還亮著
    np.fill(OFF)
    np.write()
    print("\n程式已停止，所有LED已關閉。")