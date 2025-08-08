# 實驗 #3-1：按鈕切換三段式燈號狀態
# MicroPython v1.24.0 on ESP32-DevKitC

import machine
import time

# --- 硬體腳位定義 ---
# 使用常數來定義腳位，方便管理與修改
RED_LED_PIN = 18
YELLOW_LED_PIN = 19
GREEN_LED_PIN = 21
BUTTON_PIN = 23

# --- 初始化 Pin 物件 ---
# LED 設定為輸出模式
red_led = machine.Pin(RED_LED_PIN, machine.Pin.OUT)
yellow_led = machine.Pin(YELLOW_LED_PIN, machine.Pin.OUT)
green_led = machine.Pin(GREEN_LED_PIN, machine.Pin.OUT)

# 按鈕設定為輸入模式，並使用內部下拉電阻
# 確保在按鈕未按下時，腳位維持在穩定的低電位
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)


# --- 狀態定義 ---
# 使用常數來表示不同的燈號狀態，讓程式碼更容易閱讀
STATE_GREEN = 0
STATE_YELLOW_FLASH = 1
STATE_RED = 2

# --- 變數初始化 ---
# current_state 用來追蹤目前的燈號狀態，從綠燈開始
current_state = STATE_GREEN

# last_toggle_time 用於實現非阻塞的黃燈閃爍
last_toggle_time = 0

# --- 初始狀態設定 ---
# 程式啟動時，先進入力燈恆亮的狀態
green_led.on()
yellow_led.off()
red_led.off()
print("程式啟動，目前模式：綠燈恆亮")

# --- 主迴圈 ---
while True:
    # 偵測按鈕是否被按下 (從低電位變為高電位)
    if button.value() == 1:
        # 按鈕去抖動：短暫延遲以忽略機械彈跳造成的雜訊
        time.sleep_ms(50)
        
        # 再次確認按鈕是否真的被按下
        if button.value() == 1:
            # 切換到下一個狀態
            # 使用取餘數 (%) 運算子來實現 0 -> 1 -> 2 -> 0 的循環
            current_state = (current_state + 1) % 3

            # 根據新的狀態，更新 LED 燈號並印出訊息
            if current_state == STATE_GREEN:
                green_led.on()
                yellow_led.off()
                red_led.off()
                print("模式切換：綠燈恆亮")

            elif current_state == STATE_YELLOW_FLASH:
                green_led.off()
                red_led.off()
                # 閃爍的邏輯在迴圈下方處理，這裡只需確保其他燈是關閉的
                print("模式切換：黃燈閃爍")

            elif current_state == STATE_RED:
                green_led.off()
                yellow_led.off()
                red_led.on()
                print("模式切換：紅燈恆亮")

            # 等待按鈕釋放，避免一次長按觸發多次狀態切換
            while button.value() == 1:
                time.sleep_ms(20)

    # --- 根據當前狀態執行持續性動作 ---
    # 這個區塊負責處理需要持續更新的狀態，例如閃爍
    if current_state == STATE_YELLOW_FLASH:
        # 非阻塞式閃爍邏輯
        # 取得當前時間（毫秒）
        now = time.ticks_ms()
        
        # 檢查距離上次切換黃燈狀態是否已超過 500 毫秒
        if time.ticks_diff(now, last_toggle_time) >= 500:
            # 切換黃燈狀態 (亮 -> 暗, 暗 -> 亮)
            # 因為 machine.Pin 沒有 toggle()，我們手動實現
            yellow_led.value(not yellow_led.value())
            
            # 更新上次切換的時間
            last_toggle_time = now

    # 在迴圈中加入一個微小的延遲，可以降低 CPU 使用率
    time.sleep_ms(10)