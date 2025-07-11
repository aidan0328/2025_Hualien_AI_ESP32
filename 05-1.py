# 實驗 #5-1：使用可變電阻調整LED的明亮度

# ----------------------------------------------------
# 匯入所需模組
# ----------------------------------------------------
import machine
import time
from collections import deque

# ----------------------------------------------------
# 硬體腳位與常數設定
# ----------------------------------------------------
# 可變電阻連接的 ADC 腳位
VR_PIN = 36

# 綠色 LED 連接的 GPIO 腳位
GREEN_LED_PIN = 21

# 移動平均的樣本數
ADC_SAMPLES = 10

# ADC 的最大讀值 (ESP32 為 12-bit: 2^12 - 1 = 4095)
ADC_MAX_VALUE = 4095

# PWM 的最大 duty cycle 值 (duty_u16 使用 16-bit: 2^16 - 1 = 65535)
PWM_MAX_DUTY = 65535

# ----------------------------------------------------
# 硬體初始化
# ----------------------------------------------------
# 1. 初始化 ADC
# 設定 ADC 腳位
adc_pin = machine.Pin(VR_PIN, machine.Pin.IN)
# 建立 ADC 物件
adc = machine.ADC(adc_pin)
# 設定衰減，ATTN_11DB 對應 0V-3.3V 的完整電壓範圍
adc.atten(machine.ADC.ATTN_11DB) 

# 2. 初始化綠色 LED 的 PWM
# 設定 LED 腳位為輸出
green_led_pin = machine.Pin(GREEN_LED_PIN, machine.Pin.OUT)
# 建立 PWM 物件，頻率設定為 1000 Hz 以避免人眼閃爍感
green_pwm = machine.PWM(green_led_pin, freq=1000)

# ----------------------------------------------------
# 移動平均初始化
# ----------------------------------------------------
# 使用 deque (雙向佇列) 來儲存最新的10筆讀值，它比 list 更有效率
# 當超過 maxlen 時，最舊的資料會自動被移除
adc_readings = deque((), ADC_SAMPLES)

print("實驗 #5-1 開始，請旋轉可變電阻...")

# ----------------------------------------------------
# 主迴圈
# ----------------------------------------------------
try:
    while True:
        # 1. 讀取 ADC 的原始值 (0-4095)
        current_reading = adc.read()
        
        # 2. 將新讀值加入 deque 中進行平滑處理
        adc_readings.append(current_reading)
        
        # 3. 計算移動平均值
        smoothed_adc_value = sum(adc_readings) / len(adc_readings)
        
        # 4. 將平滑後的 ADC 值 (0-4095) 映射到 PWM 的 duty cycle (0-65535)
        # 這是線性的轉換：(輸入值 / 輸入範圍) * 輸出範圍
        duty_cycle = int((smoothed_adc_value / ADC_MAX_VALUE) * PWM_MAX_DUTY)
        
        # 5. 設定 LED 的亮度
        # 使用 duty_u16() 可以提供更精細的 16-bit 亮度控制
        green_pwm.duty_u16(duty_cycle)
        
        # 6. (可選) 在終端機印出資訊，方便除錯與觀察
        print(f"原始 ADC: {current_reading:4d}, 平滑後 ADC: {int(smoothed_adc_value):4d}, PWM Duty: {duty_cycle:5d}")
        
        # 7. 短暫延遲，避免迴圈過快，降低 CPU 負載
        time.sleep_ms(50) # 每秒讀取 20 次

except KeyboardInterrupt:
    # 當按下 Ctrl+C 時，優雅地關閉程式
    print("程式已停止。")
    # 關閉 PWM，確保 LED 熄滅
    green_pwm.deinit()