# ----------------------------------------------------------------------
# 實驗 #2-6：左右來回的呼吸燈動畫（每顆2秒）
#
# 說明：
# 透過 PWM 控制 LED 亮度，實現紅、黃、綠燈的呼吸燈效果。
# 動畫順序為 R -> Y -> G -> Y -> R ... 形成來回擺動的視覺效果。
# 每顆 LED 的一次完整呼吸（漸亮至漸暗）時間為 2 秒。
#
# 執行環境：
# MicroPython v1.24.0 on ESP32-DevKitC
# ----------------------------------------------------------------------

import machine
import time

# --- 硬體接線設定 ---
# 紅綠燈 LED 模組接腳
PIN_R = 18  # 紅燈 (Red)
PIN_Y = 19  # 黃燈 (Yellow)
PIN_G = 21  # 綠燈 (Green)

# --- PWM 設定 ---
# 設定 PWM 頻率 (1000Hz 是一個不錯的選擇，可避免人眼可見的閃爍)
PWM_FREQ = 1000

# 初始化 PWM 物件，並設定初始佔空比為 0 (燈滅)
# machine.PWM(Pin, freq, duty_u16)
# duty_u16 範圍: 0 (0%) 到 65535 (100%)
led_r = machine.PWM(machine.Pin(PIN_R), freq=PWM_FREQ, duty_u16=0)
led_y = machine.PWM(machine.Pin(PIN_Y), freq=PWM_FREQ, duty_u16=0)
led_g = machine.PWM(machine.Pin(PIN_G), freq=PWM_FREQ, duty_u16=0)

# --- 核心功能函式 ---

def breathe_led(pwm_obj, duration_s=2, steps=100):
    """
    控制單顆 LED 完成一次呼吸（漸亮到漸暗）
    
    :param pwm_obj: 要控制的 machine.PWM 物件
    :param duration_s: 一次完整呼吸的總時間（秒）
    :param steps: 亮度變化的級數，級數越高越平滑
    """
    # 呼吸分為兩部分：漸亮 (fade in) 和 漸暗 (fade out)
    # 所以每部分的時間為總時間的一半
    fade_time_ms = (duration_s / 2) * 1000
    
    # 計算每一步亮度變化的延遲時間（毫秒）
    delay_ms = int(fade_time_ms / steps)
    if delay_ms < 1:
        delay_ms = 1 # 確保至少有 1ms 延遲

    # --- 漸亮 (Fade In) ---
    for i in range(steps):
        # duty_u16 的值是 16-bit，範圍 0-65535
        # 計算當前亮度的佔空比
        duty = int((i + 1) / steps * 65535)
        pwm_obj.duty_u16(duty)
        time.sleep_ms(delay_ms)

    # --- 漸暗 (Fade Out) ---
    for i in range(steps):
        # 從全亮逐漸變暗
        duty = int((steps - i - 1) / steps * 65535)
        pwm_obj.duty_u16(duty)
        time.sleep_ms(delay_ms)
        
    # 確保最後燈是完全關閉的
    pwm_obj.duty_u16(0)

# --- 主程式迴圈 ---

# 建立一個 LED 序列，這個順序可以完美實現來回循環
# R -> Y -> G -> Y -> (重複)
led_sequence = [led_r, led_y, led_g, led_y]

print("實驗 #2-6：左右來回的呼吸燈動畫")
print("動畫開始... 按下 Ctrl+C 停止程式。")

try:
    while True:
        # 依序點亮序列中的每一顆燈
        for led in led_sequence:
            # 呼叫呼吸函式，每顆燈的呼吸時間為 2 秒
            breathe_led(led, duration_s=2)
            
except KeyboardInterrupt:
    print("\n程式已手動停止。")
    # 清理資源，關閉所有 PWM 腳位
    led_r.deinit()
    led_y.deinit()
    led_g.deinit()
    print("PWM 資源已釋放。")