# 實驗 #2-5：從左到右的呼吸燈效果
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import time

# --- 硬體接線設定 ---
# 紅燈 (R): GPIO18
# 黃燈 (Y): GPIO19
# 綠燈 (G): GPIO21

# --- 初始化 PWM 物件 ---
# 設定 PWM 頻率為 1000 Hz，可避免人眼可見的閃爍
# ESP32 的 PWM duty 解析度為 10-bit，範圍是 0 (全暗) 到 1023 (全亮)
try:
    pwm_r = machine.PWM(machine.Pin(18), freq=1000)
    pwm_y = machine.PWM(machine.Pin(19), freq=1000)
    pwm_g = machine.PWM(machine.Pin(21), freq=1000)
except ValueError as e:
    print(f"錯誤：無法初始化 PWM。請檢查 GPIO 接腳是否支援 PWM。 ({e})")
    # 如果初始化失敗，可以選擇退出或用其他方式處理
    # 在 Thonny 中，通常可以直接停止程式
    raise SystemExit

def breathe(pwm_led, speed_ms=2):
    """
    讓指定的 LED 完成一次呼吸（漸亮 -> 漸暗）
    :param pwm_led: 要控制的 machine.PWM 物件
    :param speed_ms: 每一步亮度變化的延遲時間（毫秒），數值越小呼吸越快
    """
    # 漸亮 (Fade In)
    # 將 duty cycle 從 0 (暗) 增加到 1023 (最亮)
    for i in range(0, 1024):
        pwm_led.duty(i)
        time.sleep_ms(speed_ms)

    # 漸暗 (Fade Out)
    # 將 duty cycle 從 1023 (最亮) 減少到 0 (暗)
    for i in range(1023, -1, -1):
        pwm_led.duty(i)
        time.sleep_ms(speed_ms)

# --- 主程式 ---
# 使用 try...finally 結構確保程式被中斷時能正確關閉 PWM
try:
    print("程式開始：從左到右的呼吸燈效果")
    print("按下 Ctrl+C 可中斷程式。")
    
    while True:
        # 1. 紅燈呼吸
        print("紅燈 (R) 呼吸...")
        breathe(pwm_r)
        
        # 2. 黃燈呼吸
        print("黃燈 (Y) 呼吸...")
        breathe(pwm_y)
        
        # 3. 綠燈呼吸
        print("綠燈 (G) 呼吸...")
        breathe(pwm_g)

except KeyboardInterrupt:
    print("程式被使用者中斷。")

finally:
    # 程式結束或中斷時，關閉所有 PWM 輸出以釋放資源
    print("正在清理資源...")
    pwm_r.deinit()
    pwm_y.deinit()
    pwm_g.deinit()
    print("PWM 已關閉，程式結束。")