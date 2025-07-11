# 實驗 #3-2：按鈕切換呼吸燈方向（左右變化）
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import time

# --- 硬體接線設定 ---
# 按鈕接至 GPIO23（按下時為高電位，因此使用內部下拉電阻）
BUTTON_PIN = 23
# LED 模組（從左到右）
LED_R_PIN = 18  # 紅燈 (R)
LED_Y_PIN = 19  # 黃燈 (Y)
LED_G_PIN = 21  # 綠燈 (G)

# --- 初始化硬體物件 ---
# 設定按鈕為輸入，並啟用內部下拉電阻
# 當按鈕未按下時，讀取到的值為 0 (低電位)
# 當按鈕按下時，讀取到的值為 1 (高電位)
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# 設定 LED 為 PWM 輸出，以控制亮度
# ESP32 的 PWM 解析度為 10-bit，duty 範圍為 0 (滅) 到 1023 (最亮)
# 頻率設定為 1000Hz，避免人眼可見的閃爍
pwm_r = machine.PWM(machine.Pin(LED_R_PIN), freq=1000, duty=0)
pwm_y = machine.PWM(machine.Pin(LED_Y_PIN), freq=1000, duty=0)
pwm_g = machine.PWM(machine.Pin(LED_G_PIN), freq=1000, duty=0)

# 將 PWM 物件放入一個列表中，方便依序控制
# 順序：左 -> 右 (R -> Y -> G)
leds = [pwm_r, pwm_y, pwm_g]

# --- 全域狀態變數 ---
# True:  從左到右 (R -> Y -> G)
# False: 從右到左 (G -> Y -> R)
direction_forward = True

# 用於按鈕去彈跳 (debounce)
last_interrupt_time = 0

# --- 核心函式 ---
def breathe(pwm_led):
    """
    讓單顆 LED 執行一次完整的呼吸效果 (漸亮 -> 漸暗)。
    :param pwm_led: 要控制的 LED 的 PWM 物件。
    """
    # 漸亮 (Fade In)
    # 步長(step)設為 5，讓動畫更平滑且速度適中
    for duty in range(0, 1024, 5):
        pwm_led.duty(duty)
        time.sleep_ms(10)

    # 漸暗 (Fade Out)
    for duty in range(1023, -1, -5):
        pwm_led.duty(duty)
        time.sleep_ms(10)

def handle_button_press(pin):
    """
    按鈕中斷處理函式 (Interrupt Service Routine)。
    當按鈕被按下時觸發，用來反轉呼吸燈方向。
    """
    global direction_forward, last_interrupt_time
    
    current_time = time.ticks_ms()
    # 去彈跳：確保兩次有效按鈕觸發間隔超過 200ms
    if time.ticks_diff(current_time, last_interrupt_time) > 200:
        direction_forward = not direction_forward  # 反轉方向
        print("--- 按鈕觸發！方向已改變。新方向: {} ---".format("R->Y->G" if direction_forward else "G->Y->R"))
        last_interrupt_time = current_time

# --- 設定中斷 ---
# 當按鈕引腳電位從低變高 (IRQ_RISING) 時，觸發 handle_button_press 函式
button.irq(trigger=machine.Pin.IRQ_RISING, handler=handle_button_press)


# --- 主程式 ---
print("程式開始，初始方向: R -> Y -> G")
print("請按按鈕來改變呼吸燈方向。")

try:
    while True:
        if direction_forward:
            # 正向：從左到右 (R -> Y -> G)
            print("目前序列: R -> Y -> G")
            for led_pwm in leds:
                breathe(led_pwm)
        else:
            # 反向：從右到左 (G -> Y -> R)
            print("目前序列: G -> Y -> R")
            # 使用 reversed() 來反轉列表的遍歷順序
            for led_pwm in reversed(leds):
                breathe(led_pwm)

except KeyboardInterrupt:
    print("\n程式被手動中斷。")

finally:
    # 程式結束前的清理工作
    print("正在清理資源，關閉所有 LED...")
    for pwm in leds:
        pwm.deinit()  # 關閉 PWM 功能
    print("清理完畢。")