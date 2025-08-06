# ----------------------------------------------------------------------
# 實驗 #1-2：透過按鈕控制 LED 閃爍速度
#
# 執行環境：
#   - MicroPython v1.24.0
#   - ESP32-DevKitC
#
# 硬體接線：
#   - 按鈕：GPIO23 (按下時為高電位)
#   - 內建 LED：GPIO2
#
# 實驗目標：
#   - 初始狀態下，LED 每 0.1 秒閃爍一次。
#   - 每按一次按鈕，延長閃爍間隔 0.2 秒。
#   - 當閃爍間隔增加至 2 秒時，重置回 0.1 秒。
# ----------------------------------------------------------------------

# -*- coding: utf-8 -*-

# 引入必要的模組
import machine
import time

# --- 硬體腳位定義 ---
# 定義內建 LED 的腳位 (GPIO2) 為輸出模式
led = machine.Pin(2, machine.Pin.OUT)
# 定義按鈕的腳位 (GPIO23) 為輸入模式，並啟用內部下拉電阻
# 啟用下拉電阻(PULL_DOWN)後，當按鈕未按下時，腳位會穩定在低電位(0)
# 當按鈕按下時，根據接線，腳位會變為高電位(1)
button = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_DOWN)

# --- 變數初始化 ---
# 初始閃爍間隔時間 (單位：秒)
delay_time = 0.1

# 用於按鈕防抖動 (Debouncing) 處理
# 紀錄按鈕上一次的狀態，0 代表未按下，1 代表已按下
last_button_state = 0

# --- 程式開始 ---
# 在 Thonny Shell 中印出初始狀態訊息
print("程式啟動，初始閃爍間隔：" + str(delay_time) + " 秒")

# 進入主迴圈
while True:
    # 1. 偵測按鈕狀態
    current_button_state = button.value()

    # 判斷按鈕是否被「按下」的那一瞬間 (從低電位變為高電位)
    # 這樣可以避免按鈕一直按著時，程式碼連續執行
    if current_button_state == 1 and last_button_state == 0:
        # 延長閃爍間隔 0.2 秒
        delay_time = delay_time + 0.2
        
        # 使用 str() 將浮點數轉換為字串來進行拼接
        print("按鈕已按下！新的閃爍間隔：" + str(round(delay_time, 1)) + " 秒")

        # 檢查閃爍間隔是否達到或超過 2 秒
        if delay_time >= 2.0:
            # 如果是，就重置回 0.1 秒
            delay_time = 0.1
            print("閃爍間隔已達上限，重置為 0.1 秒")
    
    # 更新按鈕最後的狀態，為下一次迴圈做準備
    last_button_state = current_button_state

    # 2. 控制 LED 閃爍
    # 讀取目前 LED 的狀態 (0 或 1)，然後設定為相反的狀態，實現 "toggle" 功能
    led.value(not led.value())

    # 3. 等待指定的間隔時間
    # time.sleep() 的參數是秒，可以直接使用 delay_time
    # 也可以使用 time.sleep_ms()，參數是毫秒(整數)，需轉換：int(delay_time * 1000)
    time.sleep(delay_time)