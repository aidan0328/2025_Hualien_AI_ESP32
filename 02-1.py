# 🧪 實驗 #2-1：從左到右的跑馬燈
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

# 引入必要的函式庫
# machine 用於控制硬體，例如 GPIO 接腳
# time 用於提供延遲功能，例如 sleep
import machine
import time

# --- 硬體接腳定義 ---
# 根據實驗說明，定義紅、黃、綠 LED 連接的 GPIO 編號
# 使用大寫變數名稱是良好的程式習慣，表示這是一個固定的設定值
RED_PIN = 18
YELLOW_PIN = 19
GREEN_PIN = 21

# --- 初始化 LED 物件 ---
# 透過 machine.Pin() 函式來建立 Pin 物件，以便控制 GPIO
# 第二個參數 machine.Pin.OUT 表示我們將這些接腳設定為「輸出模式」
print("正在初始化 GPIO 接腳...")
red_led = machine.Pin(RED_PIN, machine.Pin.OUT)
yellow_led = machine.Pin(YELLOW_PIN, machine.Pin.OUT)
green_led = machine.Pin(GREEN_PIN, machine.Pin.OUT)
print("GPIO 初始化完成！")

# --- 定義跑馬燈延遲時間 ---
# 燈號亮起的持續時間（秒），可以修改這個值來改變跑馬燈的速度
delay_time = 0.5

# --- 主程式迴圈 ---
print("跑馬燈程式開始執行... 在 Thonny Shell 中按下 Ctrl+C 可以停止程式。")

try:
    # 使用 while True 建立一個無限迴圈，讓跑馬燈效果持續播放
    while True:
        # 步驟 1: 點亮紅燈 (R)
        print("亮：紅燈 (R)")
        red_led.on()        # 點亮紅燈 (輸出高電位)
        time.sleep(delay_time) # 等待 delay_time 秒
        red_led.off()       # 熄滅紅燈 (輸出低電位)

        # 步驟 2: 點亮黃燈 (Y)
        print("亮：黃燈 (Y)")
        yellow_led.on()     # 點亮黃燈
        time.sleep(delay_time) # 等待
        yellow_led.off()      # 熄滅黃燈

        # 步驟 3: 點亮綠燈 (G)
        print("亮：綠燈 (G)")
        green_led.on()      # 點亮綠燈
        time.sleep(delay_time) # 等待
        green_led.off()       # 熄滅綠燈

except KeyboardInterrupt:
    # 這是一個良好的程式習慣：
    # 當使用者在 Thonny 的 Shell (互動環境) 按下 Ctrl+C 時，會觸發 KeyboardInterrupt
    # 我們在這裡捕捉這個中斷，並確保所有燈在程式結束時是熄滅的
    print("\n程式已手動停止。")
    red_led.off()
    yellow_led.off()
    green_led.off()
    print("所有 LED 均已熄滅。")