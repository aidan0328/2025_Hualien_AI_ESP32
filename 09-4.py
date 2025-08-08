# 實驗 #9-4：超音波感測器結合蜂鳴器 (模擬倒車雷達)
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC
#
# 功能：
# 1. 使用 HC-SR04 超音波感測器測量距離。
# 2. 將測量到的距離即時列印到 REPL。
# 3. 根據距離改變蜂鳴器的鳴叫頻率，模擬倒車雷達。
# 4. 程式主迴圈為非阻塞式，使用 time.ticks_ms() 進行時序控制。

import machine
from machine import Pin, PWM
import time

# --- 硬體與常數定義 ---

# 超音波感測器接腳
TRIG_PIN = 27
ECHO_PIN = 13

# 蜂鳴器接腳
BUZZER_PIN = 15

# 聲音頻率 (Hz)
# C大調的 Si (B5)
NOTE_SI_C_MAJOR = 988
# F大調的 Si (E6)
NOTE_SI_F_MAJOR = 1318

# 蜂鳴器鳴叫的持續時間 (毫秒)
BEEP_DURATION_MS = 60

# 感測器讀取間隔 (毫秒)
SENSOR_READ_INTERVAL_MS = 100

# --- 初始化硬體 ---

# 設定超音波感測器接腳
trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

# 設定蜂鳴器為 PWM 輸出
buzzer = PWM(Pin(BUZZER_PIN))
buzzer.duty(0) # 初始狀態關閉蜂鳴器

# --- 功能函式 ---

def get_distance_cm():
    """
    觸發超音波感測器並計算回傳的距離（公分）。
    使用 time.sleep_us() 來產生精確的觸發脈衝。
    """
    # 產生一個 10us 的觸發訊號
    trig.value(0)
    time.sleep_us(5)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    try:
        # 等待 Echo 接腳變為高電位，並測量其持續時間
        # time_pulse_us 是測量脈衝寬度的阻塞式函式，但其時間極短，可接受
        pulse_duration = machine.time_pulse_us(echo, 1, 30000) # Timeout 30ms
    except OSError as ex:
        # 如果 time_pulse_us 超時，會引發 OSError
        pulse_duration = -1

    # 處理超時或錯誤
    if pulse_duration < 0:
        return 999 # 回傳一個極大值表示超出範圍

    # 計算距離 (音速約為 343 m/s 或 29.1 us/cm)
    # 距離 = (高電位時間 / 2) * 音速
    distance = (pulse_duration / 2) / 29.1
    return distance

# --- 主程式 ---

def run_parking_radar():
    """
    倒車雷達主程式邏輯。
    """
    print("倒車雷達系統啟動...")
    print("按下 Ctrl+C 以停止程式。")

    # 非阻塞式迴圈的時序變數
    last_sensor_read_time = 0
    last_beep_toggle_time = 0

    # 狀態變數
    is_beeping = False
    
    # 根據狀態決定的蜂鳴器參數
    beep_freq = 0
    beep_on_duration = 0
    beep_off_duration = 0
    
    # 程式主迴圈
    while True:
        now = time.ticks_ms()

        # 1. 定期讀取感測器數值
        if time.ticks_diff(now, last_sensor_read_time) >= SENSOR_READ_INTERVAL_MS:
            distance = get_distance_cm()
            print(f"當前距離: {distance:.1f} cm")
            last_sensor_read_time = now

            # 2. 根據距離決定蜂鳴器模式
            if distance <= 5: # 危險
                beep_freq = NOTE_SI_F_MAJOR
                beep_on_duration = 1000 # 持續響
                beep_off_duration = 0
            elif distance <= 15: # 小心
                beep_freq = NOTE_SI_C_MAJOR
                beep_on_duration = BEEP_DURATION_MS
                beep_off_duration = int(1000 / 15) - BEEP_DURATION_MS
            elif distance <= 30: # 注意
                beep_freq = NOTE_SI_C_MAJOR
                beep_on_duration = BEEP_DURATION_MS
                beep_off_duration = int(1000 / 5) - BEEP_DURATION_MS
            else: # 安全
                beep_freq = NOTE_SI_C_MAJOR
                beep_on_duration = BEEP_DURATION_MS
                beep_off_duration = int(1000 / 1) - BEEP_DURATION_MS
        
        # 3. 非阻塞式地控制蜂鳴器鳴叫
        if beep_freq > 0:
            if is_beeping:
                # 如果蜂鳴器正在響，檢查是否達到鳴叫時間
                if time.ticks_diff(now, last_beep_toggle_time) >= beep_on_duration:
                    buzzer.duty(0) # 停止鳴叫
                    is_beeping = False
                    last_beep_toggle_time = now
            else:
                # 如果蜂鳴器沒在響，檢查是否達到間隔時間
                if time.ticks_diff(now, last_beep_toggle_time) >= beep_off_duration:
                    buzzer.freq(beep_freq)
                    buzzer.duty(512) # 開始鳴叫 (50% duty cycle)
                    is_beeping = True
                    last_beep_toggle_time = now

# --- 程式進入點 ---

if __name__ == "__main__":
    try:
        run_parking_radar()
    except KeyboardInterrupt:
        print("程式已停止。")
    finally:
        # 確保程式結束時關閉蜂鳴器
        buzzer.deinit()
        print("蜂鳴器已關閉，資源已釋放。")