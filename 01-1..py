# ----------------------------------------------------------------------
# 實驗 #1-1：按鈕觸發 LED 亮滅切換
#
# 說明：
# 每當按鈕被按下一次，就切換內建 LED 的狀態（亮→滅 或 滅→亮）。
# 這個程式使用了「輪詢 (Polling)」與「延時去抖動 (Debouncing)」的方法來偵測按鈕。
#
# 硬體：
# - ESP32 開發板
# - 按鈕接到 GPIO23 與 GND
# - 內建 LED 在 GPIO2
#
# 執行方式：
# 將此程式碼儲存到 ESP32 上 (例如命名為 main.py)，
# 然後按下板上的 RST 按鈕或在 Thonny 中點擊 "執行目前腳本"。
# 按下外接的按鈕，觀察 Thonny Shell/REPL 的輸出與板上 LED 的變化。
# ----------------------------------------------------------------------

# 導入所需的模組
import machine
import time

# --- 1. 硬體初始化 ---

# 初始化 LED 接腳 (GPIO2) 為輸出模式
# ESP32 DevKitC 上的內建藍色 LED 通常位於 GPIO2
led = machine.Pin(2, machine.Pin.OUT)

# 初始化按鈕接腳 (GPIO23) 為輸入模式，並啟用內部上拉電阻
# Pin.PULL_UP: 當按鈕未按下時，接腳電位為高電位 (1)；
#              當按鈕按下時 (接腳被連接到GND)，接腳電位為低電位 (0)。
button = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)

# --- 2. 主迴圈 ---
print("程式已啟動，請按下按鈕來切換 LED 狀態...")

# 建立一個無限迴圈來持續偵測按鈕狀態
while True:
    # 檢查按鈕是否被按下 (讀取到的值為 0)
    if button.value() == 0:
        # --- 按鈕去抖動 (Debouncing) ---
        # 物理按鈕在按下和放開的瞬間，接點會快速彈跳，
        # 導致在極短時間內產生多次訊號變化。
        # 為了避免一次按壓被誤判為多次，我們加入一個短暫延遲。
        time.sleep_ms(50) # 延遲 50 毫秒

        # 延遲後再次確認按鈕是否仍然被按下，以確保這不是雜訊
        if button.value() == 0:
            # --- 切換 LED 狀態 ---
            # led.value() 會讀取目前 LED 的狀態 (1 代表亮, 0 代表滅)
            # not led.value() 會將其反轉 (1 -> 0, 0 -> 1)
            # 然後我們將反轉後的值寫回給 LED
            led.value(not led.value())

            # 在 Thonny 的互動環境 (Shell/REPL) 中印出目前狀態
            if led.value() == 1:
                print("按鈕按下！ -> LED [亮]")
            else:
                print("按鈕按下！ -> LED [滅]")

            # --- 等待按鈕釋放 ---
            # 這是非常重要的一步！
            # 如果沒有這個迴圈，當你一直按住按鈕時，
            # 主程式會不斷地快速切換 LED 狀態，造成閃爍。
            # 這個迴圈會卡在這裡，直到你放開按鈕 (button.value() 變回 1)。
            while button.value() == 0:
                pass # 什麼都不做，只是空等

    # 稍微延遲一下，降低 CPU 使用率，但這個延遲可以很短或省略
    time.sleep_ms(10)