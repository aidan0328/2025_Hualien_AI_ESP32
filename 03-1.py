# 實驗 #3-1：按鈕切換三段式燈號狀態（綠 → 閃黃 → 紅 循環）
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

from machine import Pin
import time

# --- 硬體腳位設定 ---
# LED 模組
RED_LED_PIN = 18
YELLOW_LED_PIN = 19
GREEN_LED_PIN = 21

# 按鈕
BUTTON_PIN = 23

# --- 初始化硬體元件 ---
# 設定 LED 腳位為輸出模式
red_led = Pin(RED_LED_PIN, Pin.OUT)
yellow_led = Pin(YELLOW_LED_PIN, Pin.OUT)
green_led = Pin(GREEN_LED_PIN, Pin.OUT)

# 設定按鈕腳位為輸入模式，並啟用內建的下拉電阻
# 當按鈕按下時，GPIO23 會讀到高電位(1)；未按下時，因下拉電阻而為低電位(0)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)

# --- 狀態變數初始化 ---
# 0: 綠燈恆亮
# 1: 黃燈閃爍
# 2: 紅燈恆亮
state = 0

# 用於黃燈閃爍的計時器，實現非阻塞式延遲
last_toggle_time = 0
flash_interval = 500  # 閃爍間隔（毫秒），500ms亮/500ms滅，即每秒閃爍一次

# --- 程式初始設定 ---
# 確保一開始只有綠燈亮
print("程式啟動，初始狀態：綠燈恆亮")
green_led.on()
yellow_led.off()
red_led.off()


# --- 主迴圈 ---
while True:
    # 1. 偵測按鈕事件 (包含防抖動處理)
    if button.value() == 1:
        # 防抖動 (Debounce): 等待一小段時間，確認是否為穩定按下
        time.sleep_ms(50)
        if button.value() == 1:
            # 確認按下後，更新狀態
            state = (state + 1) % 3  # 使用取餘數運算實現 0 -> 1 -> 2 -> 0 的循環
            print(f"按鈕觸發！切換至狀態 {state}")
            
            # 等待按鈕釋放，避免在一次長按中觸發多次狀態切換
            while button.value() == 1:
                time.sleep_ms(10)

    # 2. 根據當前狀態控制 LED 燈號
    if state == 0:
        # 狀態 0: 綠燈恆亮
        green_led.on()
        yellow_led.off()
        red_led.off()
        
    elif state == 1:
        # 狀態 1: 黃燈閃爍 (非阻塞式)
        green_led.off()
        red_led.off()
        
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_toggle_time) > flash_interval:
            yellow_led.toggle()  # .toggle() 會自動反轉目前腳位的狀態 (ON -> OFF, OFF -> ON)
            last_toggle_time = current_time # 更新上次切換時間
            
    elif state == 2:
        # 狀態 2: 紅燈恆亮
        green_led.off()
        yellow_led.off()
        red_led.on()

    # 在迴圈中加入一個微小的延遲，可以降低 CPU 使用率
    time.sleep_ms(10)