# 實驗 #6-1：按鈕切換跑馬燈與呼吸燈模式＋可變電阻控制速度
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import time
from collections import deque

# --- 硬體腳位定義 ---
# 可變電阻
POT_PIN = 36
adc = machine.ADC(machine.Pin(POT_PIN))
adc.atten(machine.ADC.ATTN_11DB)  # 設定電壓範圍為 0-3.3V，對應 ADC 讀值 0-4095

# LED 模組 (使用 PWM 以同時支援開關與亮度變化)
# PWM 頻率設為 1000Hz，人眼看不出閃爍
led_pwms = [
    machine.PWM(machine.Pin(18), freq=1000), # 紅燈
    machine.PWM(machine.Pin(19), freq=1000), # 黃燈
    machine.PWM(machine.Pin(21), freq=1000)  # 綠燈
]

# 按鈕
BUTTON_PIN = 23
button = machine.Pin(BUTTON_PIN, machine.Pin.IN)

# --- 全域狀態變數 ---
# 模式控制 (0: 跑馬燈, 1: 呼吸燈)
current_mode = 0

# ADC 平滑化 (移動平均)
adc_readings = deque([0] * 10, 10) # 使用 deque 自動維持 10 筆資料

# 非阻塞式計時器
last_update_times = {
    'marquee': 0,
    'breathing': 0,
    'adc': 0
}

# 按鈕除錯 (Debouncing)
last_button_state = 0
last_press_time = 0
DEBOUNCE_MS = 200 # 按鈕觸發間隔，避免彈跳或誤觸

# 跑馬燈模式狀態
marquee_step = 0
MARQUEE_SEQUENCE = [0, 1, 2, 1] # 跑馬燈順序 R -> Y -> G -> Y -> ... (對應 led_pwms 的索引)

# 呼吸燈模式狀態
brightness = 0
fade_amount = 5 # 每次亮度變化的量

# --- 輔助函式 ---
def map_value(x, in_min, in_max, out_min, out_max):
    """將一個範圍的數值線性對應到另一個範圍"""
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def reset_leds():
    """關閉所有 LED，用於模式切換時的重置"""
    for p in led_pwms:
        p.duty(0)

def reset_mode_states():
    """重置模式相關的狀態變數，確保切換後能正常開始"""
    global marquee_step, brightness, fade_amount
    
    # 重置跑馬燈狀態
    marquee_step = 0
    
    # 重置呼吸燈狀態
    brightness = 0
    fade_amount = 5
    
    # 清空 LED 狀態
    reset_leds()
    print("-" * 20)


# --- 核心邏輯函式 ---
def handle_button(now):
    """處理按鈕事件，包含除錯與模式切換"""
    global current_mode, last_button_state, last_press_time
    
    state = button.value()
    # 偵測按鈕被按下的瞬間 (Rising Edge)
    if state == 1 and last_button_state == 0:
        # 如果距離上次有效觸發已超過除錯時間
        if time.ticks_diff(now, last_press_time) > DEBOUNCE_MS:
            last_press_time = now
            current_mode = 1 - current_mode # 在 0 和 1 之間切換
            reset_mode_states() # 重置狀態以準備新模式
            mode_name = "跑馬燈" if current_mode == 0 else "呼吸燈"
            print(f"模式切換 -> 當前模式: {mode_name}")
            
    last_button_state = state

def get_smooth_adc_period(now):
    """讀取 ADC 值，進行移動平均，並根據當前模式轉換為對應的時間週期"""
    global adc_readings
    
    # 每 20ms 讀取一次 ADC，避免過於頻繁
    if time.ticks_diff(now, last_update_times['adc']) > 20:
        last_update_times['adc'] = now
        adc_readings.append(adc.read())
    
    smooth_adc_val = sum(adc_readings) / len(adc_readings)
    
    if current_mode == 0: # 跑馬燈模式
        # ADC: 0-4095 -> 時間: 0.5s-3s (500ms-3000ms)
        return map_value(smooth_adc_val, 0, 4095, 500, 3000)
    else: # 呼吸燈模式
        # ADC: 0-4095 -> 時間: 0.1s-3s (100ms-3000ms)
        return map_value(smooth_adc_val, 0, 4095, 100, 3000)

def run_marquee(now, period):
    """執行跑馬燈邏輯 (非阻塞)"""
    global marquee_step
    
    # 一輪跑馬燈有 4 個步驟 (R, Y, G, Y)
    # 所以每一步的時間 = 總週期 / 4
    step_delay = period / 4
    
    if time.ticks_diff(now, last_update_times['marquee']) > step_delay:
        last_update_times['marquee'] = now
        
        # 關閉所有燈
        reset_leds()
        
        # 點亮當前步驟的燈
        # duty(1023) 代表全亮 (10-bit PWM)
        led_index = MARQUEE_SEQUENCE[marquee_step]
        led_pwms[led_index].duty(1023)
        
        # 移至下一步
        marquee_step = (marquee_step + 1) % len(MARQUEE_SEQUENCE)

def run_breathing(now, period):
    """執行呼吸燈邏輯 (非阻塞)"""
    global brightness, fade_amount
    
    # 呼吸週期包含一次亮起和一次熄滅
    # 亮度從 0 -> 255 再 -> 0，總共 255/fade_amount * 2 個步驟
    total_steps = (255 / abs(fade_amount)) * 2
    step_delay = period / total_steps
    
    if time.ticks_diff(now, last_update_times['breathing']) > step_delay:
        last_update_times['breathing'] = now
        
        # 更新亮度
        brightness += fade_amount
        
        # 碰到邊界時反轉方向
        if brightness <= 0:
            brightness = 0
            fade_amount = -fade_amount
        elif brightness >= 255:
            brightness = 255
            fade_amount = -fade_amount
            
        # 計算 PWM duty cycle (0-1023)
        # 為了讓視覺效果更線性，對亮度值進行平方處理 (Gamma Correction)
        duty_val = int((brightness / 255) ** 2 * 1023)
        
        # 設定所有燈的亮度
        for p in led_pwms:
            p.duty(duty_val)


# --- 主程式迴圈 ---
print("實驗 #6-1 啟動...")
print("按按鈕可在跑馬燈與呼吸燈模式間切換。")
print(f"當前模式: {'跑馬燈' if current_mode == 0 else '呼吸燈'}")

while True:
    # 獲取當前時間，整個迴圈中重複使用以確保一致性
    now = time.ticks_ms()
    
    # 1. 處理按鈕輸入
    handle_button(now)
    
    # 2. 根據可變電阻獲取當前模式所需的時間週期
    period = get_smooth_adc_period(now)
    
    # 3. 根據當前模式執行對應的 LED 效果
    if current_mode == 0:
        run_marquee(now, period)
    else: # current_mode == 1
        run_breathing(now, period)
        
    # 在主迴圈中加入一個極小的延遲，可以釋放 CPU 資源給其他系統任務
    # 但這個延遲非常小，不會影響非阻塞邏輯的響應
    time.sleep_ms(1)