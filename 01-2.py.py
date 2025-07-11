# --------------------------------------------------------------------------
# 實驗 #1-2：透過按鈕控制 LED 閃爍速度
#
# 執行環境：
#   - MicroPython v1.24.0
#   - ESP32-DevKitC
#
# 硬體接線：
#   - 按鈕：GPIO23 -> GND (使用內部上拉電阻)
#   - 內建 LED：GPIO2
#
# 實驗目標：
# 1. 初始狀態，LED 每 0.1 秒閃爍一次。
# 2. 每按一次按鈕，閃爍間隔延長 0.2 秒。
# 3. 當閃爍間隔超過 2.0 秒時，重置回 0.1 秒。
# 4. 在 Thonny 的互動環境中印出目前的閃爍間隔。
# --------------------------------------------------------------------------

import machine
import time

# --- 1. 硬體初始化 ---
# 設定 LED 連接的腳位 (GPIO2) 為輸出模式
# ESP32 DevKitC 上的內建 LED 通常在 GPIO2
led = machine.Pin(2, machine.Pin.OUT)

# 設定按鈕連接的腳位 (GPIO23) 為輸入模式
# machine.Pin.PULL_UP：啟用內部上拉電阻。
# 當按鈕未按下時，腳位會是高電位 (1)；
# 當按鈕按下接地時，腳位會是低電位 (0)。
button = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)

# --- 2. 變數初始化 ---
# 初始閃爍間隔時間（單位：秒）
blink_interval = 0.1

# 印出初始狀態
print(f"程式啟動。初始閃爍間隔: {blink_interval:.1f} 秒")

# --- 3. 主迴圈 ---
# 程式會不斷地在這個迴圈中執行
while True:
    # --- 偵測按鈕狀態 ---
    # button.value() == 0 表示按鈕被按下 (因為使用上拉電阻)
    if button.value() == 0:
        # 軟體去抖動 (Debouncing)：等待一小段時間，確保是穩定按下而不是雜訊
        time.sleep_ms(20)
        
        # 再次確認按鈕是否仍然被按下
        if button.value() == 0:
            # --- 更新閃爍間隔的邏輯 ---
            blink_interval += 0.2
            
            # 檢查是否超過 2.0 秒，若超過則重置
            # 使用 > 2.0 而不是 == 是為了避免浮點數精度問題
            if blink_interval > 2.0:
                blink_interval = 0.1
            
            # 在 Thonny 的互動環境中印出更新後的間隔時間
            # 使用 :.1f 格式化浮點數，使其只顯示一位小數
            print(f"按鈕按下！閃爍間隔更新為: {blink_interval:.1f} 秒")
            
            # 等待按鈕被釋放，避免在一次長按中觸發多次
            while button.value() == 0:
                pass # 什麼都不做，直到按鈕被放開

    # --- 控制 LED 閃爍 ---
    # 閃爍一次包含「亮」和「暗」兩個狀態
    # 讓整個亮暗循環的時間等於 blink_interval
    
    # 1. 開啟 LED
    led.value(1) # 或 led.on()
    # 2. 等待一半的間隔時間
    time.sleep(blink_interval / 2)
    
    # 3. 關閉 LED
    led.value(0) # 或 led.off()
    # 4. 再等待一半的間隔時間
    time.sleep(blink_interval / 2)