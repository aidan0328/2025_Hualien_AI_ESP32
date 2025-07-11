# ----------------------------------------------------------------
# 實驗 #2-5：從左到右的呼吸燈效果
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC
# 說明：
# 依序點亮並熄滅紅、黃、綠三色 LED，並使用 PWM 技術
# 實現平滑的漸亮與漸暗（呼吸）效果。
# ----------------------------------------------------------------

from machine import Pin, PWM
import time

# --- 硬體腳位設定 ---
# 根據實驗說明，從左到右依序為 R, Y, G
# R（紅燈）：GPIO18
# Y（黃燈）：GPIO19
# G（綠燈）：GPIO21
led_pins = [18, 19, 21]

# --- PWM 參數設定 ---
PWM_FREQ = 1000  # PWM 頻率 (Hz)，1000Hz 足以避免人眼可見的閃爍
BREATHE_DELAY_MS = 5 # 每次調整亮度的延遲時間 (毫秒)，值越小呼吸越快
BREATHE_STEP = 256   # 亮度調整的步長，值越大呼吸越快 (總步數變少)

# --- 初始化 PWM 物件 ---
# PWM (Pulse Width Modulation) 是一種透過快速開關訊號來模擬類比電壓的技術，
# 藉由調整「工作週期 (Duty Cycle)」來控制 LED 亮度。
# 我們為每一個 LED 腳位建立一個 PWM 物件。
pwm_list = []
for pin_num in led_pins:
    pin = Pin(pin_num, Pin.OUT)
    pwm = PWM(pin, freq=PWM_FREQ)
    pwm_list.append(pwm)

print("硬體初始化完成，準備開始呼吸燈效果...")

def breathe(pwm_led):
    """
    控制單一個 LED 完成一次完整的呼吸（漸亮 -> 漸暗）。
    
    參數:
    - pwm_led: 要控制的 PWM 物件。
    """
    # duty_u16 的範圍是 0 (全暗) 到 65535 (全亮)
    
    # --- 漸亮過程 (Fade In) ---
    # 使用 for 迴圈，從 0 開始，以 BREATHE_STEP 為間隔增加亮度
    for duty in range(0, 65536, BREATHE_STEP):
        pwm_led.duty_u16(duty)
        time.sleep_ms(BREATHE_DELAY_MS)

    # --- 漸暗過程 (Fade Out) ---
    # 使用 for 迴圈，從 65535 開始，以 BREATHE_STEP 為間隔降低亮度
    for duty in range(65535, -1, -BREATHE_STEP):
        pwm_led.duty_u16(duty)
        time.sleep_ms(BREATHE_DELAY_MS)
        
# --- 主程式迴圈 ---
# 使用 try...finally 結構可以確保即使程式被中斷 (例如按下 Ctrl+C)，
# finally 區塊的程式碼依然會被執行，用來安全地關閉 LED。
try:
    while True:
        # 依序對 pwm_list 中的每一個 LED 執行呼吸效果
        # 順序為：紅 -> 黃 -> 綠
        for pwm in pwm_list:
            breathe(pwm)
            time.sleep_ms(200) # 每顆燈呼吸完後，稍微停頓一下，節奏感更好

finally:
    # 清理程式：當程式結束時，釋放所有 PWM 腳位
    print("程式結束，正在關閉所有 LED...")
    for pwm in pwm_list:
        pwm.deinit() # 關閉 PWM 功能，LED 會熄滅
    print("所有腳位已釋放。")