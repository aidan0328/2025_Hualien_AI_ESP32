# ----------------------------------------------------------------
# 實驗 #2-2：從右到左的跑馬燈
#
# 說明：
# 實作一個從右到左的跑馬燈效果，依序點亮 G → Y → R 三顆 LED，
# 並且循環播放。
#
# 硬體接線：
# R (紅燈): GPIO18
# Y (黃燈): GPIO19
# G (綠燈): GPIO21
# ----------------------------------------------------------------

# 1. 導入必要的模組
from machine import Pin
import time

# 2. 定義 LED 接腳
# 根據硬體接線說明，建立 Pin 物件並設定為輸出模式 (Pin.OUT)
red_led = Pin(18, Pin.OUT)
yellow_led = Pin(19, Pin.OUT)
green_led = Pin(21, Pin.OUT)

# 3. 主程式區塊
# 使用 try...finally 結構可以確保程式被中斷時 (例如在 Thonny 按下 Ctrl+C)，
# finally 區塊的程式碼仍會被執行，用來關閉所有 LED。
try:
    print("程式開始執行，跑馬燈效果啟動... (按下 Ctrl+C 停止)")
    
    # 使用無限迴圈，讓跑馬燈效果不斷循環
    while True:
        # --- 從右到左的順序：G -> Y -> R ---
        
        # 點亮綠燈 (G)，持續 0.5 秒
        green_led.value(1)      # value(1) 代表高電位，點亮 LED
        time.sleep(0.5)         # 延遲 0.5 秒
        green_led.value(0)      # value(0) 代表低電位，熄滅 LED
        
        # 點亮黃燈 (Y)，持續 0.5 秒
        yellow_led.value(1)
        time.sleep(0.5)
        yellow_led.value(0)
        
        # 點亮紅燈 (R)，持續 0.5 秒
        red_led.value(1)
        time.sleep(0.5)
        red_led.value(0)

finally:
    # 程式結束或中斷時，確保所有 LED 都熄滅
    print("\n程式已停止，關閉所有 LED。")
    red_led.value(0)
    yellow_led.value(0)
    green_led.value(0)