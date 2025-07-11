# 實驗 #2-4：三顆 LED 同步呼吸燈效果
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import time

# --- 硬體接線設定 ---
# 根據您的接線，設定 LED 對應的 GPIO 腳位
RED_PIN = 18
YELLOW_PIN = 19
GREEN_PIN = 21

# --- PWM 參數設定 ---
PWM_FREQ = 1000  # PWM 頻率 (Hz)，1000Hz 對於人眼來說已經非常平滑，不會察覺閃爍

# --- 初始化 LED 的 PWM 物件 ---
# 1. 建立 Pin 物件
pin_r = machine.Pin(RED_PIN, machine.Pin.OUT)
pin_y = machine.Pin(YELLOW_PIN, machine.Pin.OUT)
pin_g = machine.Pin(GREEN_PIN, machine.Pin.OUT)

# 2. 建立 PWM 物件
led_r = machine.PWM(pin_r)
led_y = machine.PWM(pin_y)
led_g = machine.PWM(pin_g)

# 3. 設定所有 PWM 物件的頻率
led_r.freq(PWM_FREQ)
led_y.freq(PWM_FREQ)
led_g.freq(PWM_FREQ)

print("程式開始：三顆 LED 同步呼吸燈效果")
print(f"紅燈(R): GPIO {RED_PIN}")
print(f"黃燈(Y): GPIO {YELLOW_PIN}")
print(f"綠燈(G): GPIO {GREEN_PIN}")
print("按下 Ctrl+C 以停止程式。")

# --- 主迴圈 ---
try:
    while True:
        # 漸亮階段 (Fade In)
        # duty cycle 從 0 (全暗) 到 65535 (全亮)
        # MicroPython 的 PWM duty cycle 使用 16-bit 解析度 (0-65535)
        # 增加步長 (step) 可以讓動畫速度變快
        for duty in range(0, 65536, 128):
            led_r.duty_u16(duty)
            led_y.duty_u16(duty)
            led_g.duty_u16(duty)
            time.sleep_ms(5)  # 每個亮度等級之間的延遲，控制呼吸速度

        # 漸暗階段 (Fade Out)
        # duty cycle 從 65535 (全亮) 到 0 (全暗)
        for duty in range(65535, -1, -128):
            led_r.duty_u16(duty)
            led_y.duty_u16(duty)
            led_g.duty_u16(duty)
            time.sleep_ms(5)

except KeyboardInterrupt:
    # 當使用者按下 Ctrl+C 時，優雅地關閉程式
    print("程式已停止。")
    # 關閉 PWM 功能，釋放資源
    led_r.deinit()
    led_y.deinit()
    led_g.deinit()