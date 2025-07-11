# ----------------------------------------------------------------
# 實驗 #2-3：來回跑的跑馬燈
#
# 說明：
# 透過控制 ESP32 的 GPIO 接腳，讓紅、黃、綠三色 LED
# 產生來回移動的跑馬燈效果 (R -> Y -> G -> Y -> R ...)。
#
# MicroPython v1.24.0 on ESP32-DevKitC
# ----------------------------------------------------------------

import machine
import time

# --- 硬體接線設定 ---
# 根據您的接線，將 GPIO 編號對應到各色 LED
RED_PIN = 18    # R (紅燈)
YELLOW_PIN = 19 # Y (黃燈)
GREEN_PIN = 21  # G (綠燈)

# --- 參數設定 ---
# 每個燈亮起的延遲時間（秒），可以調整這個值來改變跑馬燈速度
delay_time = 0.2

# --- 初始化 LED 接腳 ---
# 建立 Pin 物件並設定為輸出模式 (machine.Pin.OUT)
# 並將它們放入一個列表中，方便用迴圈控制
# 列表順序：紅 -> 黃 -> 綠
leds = [
    machine.Pin(RED_PIN, machine.Pin.OUT),
    machine.Pin(YELLOW_PIN, machine.Pin.OUT),
    machine.Pin(GREEN_PIN, machine.Pin.OUT)
]

# --- 程式主體 ---
print("實驗 #2-3：來回跑的跑馬燈，程式已啟動...")
print(f"燈光順序: R({RED_PIN}) -> Y({YELLOW_PIN}) -> G({GREEN_PIN}) -> Y -> R ...")
print(f"延遲時間: {delay_time} 秒")

try:
    # 使用無限迴圈讓跑馬燈效果持續執行
    while True:
        # --- 正向：從左到右 (R -> Y -> G) ---
        # 遍歷整個 leds 列表 (索引 0, 1, 2)
        for i in range(len(leds)):
            leds[i].on()            # 點亮當前的 LED
            time.sleep(delay_time)  # 等待指定時間
            leds[i].off()           # 熄滅當前的 LED

        # --- 反向：從右到左 (Y -> R) ---
        # 為了製造 "反彈" 的效果，我們從倒數第二個燈開始往回走
        # 遍歷 leds 列表的倒數第二個到第一個 (索引 1, 0)
        # range(start, stop, step) -> range(1, -1, -1) 會產生 [1, 0]
        for i in range(len(leds) - 2, -1, -1):
            leds[i].on()            # 點亮當前的 LED
            time.sleep(delay_time)  # 等待指定時間
            leds[i].off()           # 熄滅當前的 LED

except KeyboardInterrupt:
    # 當使用者按下 Ctrl+C 時，優雅地結束程式
    print("程式已由使用者手動停止。")
    # 確保所有 LED 在程式結束時都是熄滅的
    for led in leds:
        led.off()