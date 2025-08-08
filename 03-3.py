# 實驗 #3-3：多段動態燈效模式切換器
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import time
import math

# --- 硬體設定 ---
PWM_FREQ = 1000
BUTTON_PIN = 23
RED_LED_PIN = 18
YELLOW_LED_PIN = 19
GREEN_LED_PIN = 21

# --- 初始化硬體 ---
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
leds = [
    machine.PWM(machine.Pin(RED_LED_PIN), freq=PWM_FREQ, duty=0),
    machine.PWM(machine.Pin(YELLOW_LED_PIN), freq=PWM_FREQ, duty=0),
    machine.PWM(machine.Pin(GREEN_LED_PIN), freq=PWM_FREQ, duty=0)
]

# --- 狀態與參數設定 ---
TOTAL_MODES = 4
current_mode = 0
last_button_state = 0

# 按鈕去抖動參數
DEBOUNCE_MS = 200
last_press_time = 0

# 模式 1 的狀態變數
breathing_led_index = 0
last_switch_time = 0 # 用於防止在亮度低點時重複切換

# 模式 3 的狀態變數
marquee_led_index = 0
last_marquee_time = time.ticks_ms()
MARQUEE_DELAY = 250

# --- 功能函式 ---
def all_leds_off():
    for led in leds:
        led.duty(0)

def set_all_leds_duty(duty_cycle):
    for led in leds:
        led.duty(duty_cycle)

def check_button_press():
    global current_mode, last_button_state, last_press_time
    
    mode_was_switched = False
    button_state = button.value()
    current_time = time.ticks_ms()

    if button_state == 1 and last_button_state == 0:
        if time.ticks_diff(current_time, last_press_time) > DEBOUNCE_MS:
            last_press_time = current_time
            current_mode = (current_mode + 1) % TOTAL_MODES
            print(f"模式切換至: {current_mode}")
            all_leds_off()
            mode_was_switched = True
            
    last_button_state = button_state
    return mode_was_switched

def mode_1_single_breath():
    """模式 1: 單顆 LED 呼吸燈，並輪流切換。"""
    global breathing_led_index, last_switch_time
    
    # 計算呼吸效果的亮度值 (0-1023)
    brightness = (math.sin(time.ticks_ms() * 0.002 * math.pi) + 1) / 2
    duty_cycle = int(brightness * 1023)
    
    leds[breathing_led_index].duty(duty_cycle)

    # 檢查是否完成一個呼吸週期 (亮度接近最低點)
    if duty_cycle < 10:
        # 使用計時器防止在低亮度區間內重複觸發切換
        if time.ticks_diff(time.ticks_ms(), last_switch_time) > 1000:
            last_switch_time = time.ticks_ms() # 更新切換時間戳
            
            # 將剛完成呼吸的 LED 明確關閉
            leds[breathing_led_index].duty(0)
            
            # 更新索引，準備下一顆 LED
            breathing_led_index = (breathing_led_index + 1) % len(leds)
            
def mode_2_sync_breath():
    """模式 2: 三顆 LED 同步呼吸燈"""
    brightness = (math.sin(time.ticks_ms() * 0.002 * math.pi) + 1) / 2
    duty_cycle = int(brightness * 1023)
    set_all_leds_duty(duty_cycle)

def mode_3_marquee():
    """模式 3: 跑馬燈效果"""
    global marquee_led_index, last_marquee_time
    if time.ticks_diff(time.ticks_ms(), last_marquee_time) >= MARQUEE_DELAY:
        last_marquee_time = time.ticks_ms()
        all_leds_off()
        current_led = leds[len(leds) - 1 - marquee_led_index]
        current_led.duty(1023)
        marquee_led_index = (marquee_led_index + 1) % len(leds)

# --- 主程式迴圈 ---
print("燈效模式切換器已啟動，模式: 0")

try:
    while True:
        mode_switched = check_button_press()
        
        # 當模式切換時，重置相關狀態變數
        if mode_switched:
            if current_mode == 1:
                breathing_led_index = 0
                last_switch_time = time.ticks_ms()
            elif current_mode == 3:
                marquee_led_index = 0
                last_marquee_time = time.ticks_ms()
            continue
            
        # 根據模式執行對應函式
        if current_mode == 1:
            mode_1_single_breath()
        elif current_mode == 2:
            mode_2_sync_breath()
        elif current_mode == 3:
            mode_3_marquee()
        
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("程式已停止")

finally:
    all_leds_off()
    print("所有 LED 已關閉")