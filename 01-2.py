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

import machine
import utime

# --- 1. 硬體腳位設定 ---
# 設定內建 LED (GPIO2) 為輸出模式
led = machine.Pin(2, machine.Pin.OUT)
# 設定按鈕 (GPIO23) 為輸入模式
# 根據題目「按下時為高電位」，我們不需要設定上拉或下拉電阻
button = machine.Pin(23, machine.Pin.IN)

# --- 2. 狀態變數 ---
# 用於控制 LED 閃爍的間隔時間（單位：秒）
# 初始值設為 0.1 秒
blink_interval = 0.1

# 用於非阻塞式閃爍的時間戳記
# 記錄上次 LED 狀態切換的時間
last_toggle_time = 0

# 用於按鈕防抖 (Debouncing)
# 記錄按鈕上一次的狀態，以偵測狀態變化 (按下瞬間)
last_button_state = 0

# --- 3. 初始狀態訊息 ---
print("實驗 #1-2 啟動...")
print(f"初始閃爍間隔: {blink_interval:.1f} 秒")

# --- 4. 主迴圈 ---
while True:
    # --- 程式區塊 A: 處理按鈕輸入 (包含防抖) ---

    # 讀取按鈕目前狀態 (0: 未按下, 1: 已按下)
    current_button_state = button.value()

    # 偵測「按下」的瞬間 (從 0 變到 1)
    # 這是為了確保按住按鈕不放時，只觸發一次事件
    if current_button_state == 1 and last_button_state == 0:
        # 短暫延遲 20 毫秒，濾掉機械彈跳產生的雜訊
        utime.sleep_ms(20)
        # 再次確認按鈕是否仍被按下
        if button.value() == 1:
            # 更新閃爍間隔
            blink_interval += 0.2

            # 檢查是否達到重置條件
            # 使用 >= 2.0 而不是 == 2.0 是為了避免浮點數精度問題
            if blink_interval >= 2.0:
                blink_interval = 0.1

            # 為了讓輸出的數字更漂亮，四捨五入到小數點後一位
            blink_interval = round(blink_interval, 1)

            # 在 Thonny 的互動環境中印出新的間隔時間
            print(f"按鈕觸發！閃爍間隔更新為: {blink_interval:.1f} 秒")

    # 更新按鈕的最後狀態，為下一次迴圈做準備
    last_button_state = current_button_state

    # --- 程式區塊 B: 控制 LED 閃爍 (非阻塞式) ---

    # 取得目前時間戳記 (毫秒)
    current_time_ms = utime.ticks_ms()

    # 計算自上次閃爍以來經過的時間
    # blink_interval * 1000 將秒轉換為毫秒
    if utime.ticks_diff(current_time_ms, last_toggle_time) > (blink_interval * 1000):
        # 如果經過的時間超過設定的間隔，就切換 LED 狀態
        led.toggle()  # .toggle() 會自動反轉目前狀態 (ON -> OFF, OFF -> ON)
        # 更新最後閃爍的時間戳記為現在
        last_toggle_time = current_time_ms