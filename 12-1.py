# -*- coding: UTF-8 -*-

# 🧪 實驗 #12-1： 使用可變電阻轉動伺服馬達
# ----------------------------------------------------
# 執行環境：
#   - MicroPython v1.24.0
#   - ESP32-DevKitC
# 硬體接線：
#   - 可變電阻(VR) -> GPIO36 (ADC1_CH0)
#   - SG90 伺服馬達 -> GPIO22
# ----------------------------------------------------

from machine import Pin, ADC, PWM
import time

# --- 硬體與參數設定 ---
# 可變電阻連接的 ADC 引腳
VR_PIN = 36
# 伺服馬達連接的 PWM 引腳
SERVO_PIN = 22

# 伺服馬達 PWM 頻率 (標準伺服馬達通常為 50Hz)
SERVO_FREQ = 50

# ESP32 ADC 的解析度為 12-bit，所以範圍是 0-4095
ADC_MIN = 0
ADC_MAX = 4095

# SG90 伺服馬達的脈衝寬度範圍 (單位: 微秒 us)
# 0   度角 -> 約 500us
# 180 度角 -> 約 2500us
# 注意：不同廠牌的伺服馬達可能有些微差異，可微調此處數值
SERVO_MIN_PULSE_US = 500
SERVO_MAX_PULSE_US = 2500

# --- 核心函式 ---

def map_value(x, in_min, in_max, out_min, out_max):
    """
    將一個數值從一個範圍線性對應到另一個範圍。
    (線性插值法)
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def pulse_us_to_duty_u16(pulse_us, freq=50):
    """
    將指定的脈衝寬度(us)轉換為 PWM 的 duty_u16 數值。
    duty_u16 的範圍是 0 - 65535。
    """
    # 計算 PWM 週期 (單位: us)
    period_us = 1_000_000 / freq
    # 計算 duty cycle
    duty_cycle = pulse_us / period_us
    # 轉換為 16-bit 的 duty value
    return int(duty_cycle * 65535)

# --- 硬體初始化 ---

# 1. 初始化 ADC
# 設定 ADC Pin
vr_pin_obj = Pin(VR_PIN, Pin.IN)
# 建立 ADC 物件
vr_adc = ADC(vr_pin_obj)
# 設定衰減，讓 ADC 可以讀取 0V-3.3V 的完整電壓範圍
vr_adc.atten(ADC.ATTN_11DB)
# 設定 ADC 解析度為 12-bit (0-4095)
vr_adc.width(ADC.WIDTH_12BIT)

# 2. 初始化 PWM
# 建立 PWM 物件
servo_pwm = PWM(Pin(SERVO_PIN, Pin.OUT), freq=SERVO_FREQ)

print("✅ 伺服馬達與可變電阻初始化完成。")
print("開始轉動可變電阻來控制伺服馬達...")

# --- 主迴圈 ---

try:
    while True:
        # 1. 讀取可變電阻的 ADC 數值 (0-4095)
        adc_value = vr_adc.read()

        # 2. 將 ADC 數值對應到伺服馬達的脈衝寬度 (500us - 2500us)
        pulse_width = map_value(adc_value, ADC_MIN, ADC_MAX, SERVO_MIN_PULSE_US, SERVO_MAX_PULSE_US)

        # 3. 將脈衝寬度轉換為 PWM 的 duty_u16 數值
        duty = pulse_us_to_duty_u16(pulse_width, SERVO_FREQ)

        # 4. 設定伺服馬達的 PWM duty cycle，使其轉動到對應角度
        servo_pwm.duty_u16(duty)
        
        # 為了避免迴圈過快消耗過多CPU資源，可以加入一個極短的延遲。
        # 這個延遲時間(20ms)剛好等於伺服馬達的一個控制週期(50Hz)，
        # 既能穩定控制，也符合非阻塞的精神。
        time.sleep_ms(20)

except KeyboardInterrupt:
    print("\n⏹️ 偵測到使用者中斷程式...")

finally:
    # 程式結束時，釋放 PWM 資源，停止發送訊號
    servo_pwm.deinit()
    print("PWM 資源已釋放，程式安全結束。")