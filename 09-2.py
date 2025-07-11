# ----------------------------------------------------------------------
# 實驗 #9-2：蜂鳴器發出Do Re Mi (非阻塞式)
#
# 執行環境：
#   - MicroPython v1.24.0
#   - ESP32-DevKitC
#
# 功能說明：
#   - 非阻塞式設計，不使用 sleep()。
#   - 蜂鳴器依序播放 Do, Re, Mi, Fa, Sol, La, Si。
#   - 每個音符持續 0.5 秒，播放完畢後停頓 2 秒。
#   - 短按按鈕 (<1秒) 可暫停/繼續播放。
#   - 長按按鈕 (>3秒) 可切換大調 (C -> D -> E -> F -> G -> A -> C...)。
# ----------------------------------------------------------------------

import machine
import utime

# --- 1. 硬體設定 ---
# 蜂鳴器連接到 GPIO 15
BUZZER_PIN = 15
# 按鈕連接到 GPIO 23
BUTTON_PIN = 23

# 初始化蜂鳴器為 PWM 物件
# PWM (Pulse-Width Modulation) 用於產生不同頻率的音高
buzzer_pwm = machine.PWM(machine.Pin(BUZZER_PIN))
# 先關閉蜂鳴器
buzzer_pwm.duty(0)

# 初始化按鈕
# Pin.IN: 設定為輸入模式
# Pin.PULL_DOWN: 使用內部下拉電阻，確保按鈕未按下時為穩定的低電位(0)
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# --- 2. 常數定義 ---
# 音符持續時間 (毫秒)
NOTE_DURATION_MS = 500
# 音階結束後的停頓時間 (毫秒)
PAUSE_DURATION_MS = 2000
# 長按的判定時間 (毫秒)
LONG_PRESS_MS = 3000
# 短按的最大時間 (毫秒)
SHORT_PRESS_MS = 1000
# 蜂鳴器PWM工作週期 (0-1023)，512 代表 50% 的方波，音量適中
DUTY_CYCLE = 512

# --- 3. 音樂資料 ---
# 定義音符頻率 (Hz)
# 0 代表休止符，但在這裡我們用程式邏輯來控制靜音
NOTES = {
    # C 大調 (C4)
    "C": [262, 294, 330, 349, 392, 440, 494],
    # D 大調
    "D": [294, 330, 370, 392, 440, 494, 554],
    # E 大調
    "E": [330, 370, 415, 440, 494, 554, 622],
    # F 大調
    "F": [349, 392, 440, 466, 523, 587, 659],
    # G 大調
    "G": [392, 440, 494, 523, 587, 659, 740],
    # A 大調
    "A": [440, 494, 554, 587, 659, 740, 831],
}
# 大調的播放順序
SCALE_ORDER = ["C", "D", "E", "F", "G", "A"]

# --- 4. 狀態變數 ---
# 播放控制
is_paused = False
current_scale_index = 0
current_note_index = 0 # 0-6 代表音符, 7 代表音階後的停頓

# 時間追蹤 (使用 utime.ticks_ms 來避免32位元整數溢位問題)
last_event_time = utime.ticks_ms()

# 按鈕狀態追蹤
button_press_time = 0
last_button_state = 0
long_press_triggered = False

print("實驗 #9-2 啟動：蜂鳴器音階播放器")
print(f"目前音階: {SCALE_ORDER[current_scale_index]} 大調")

# --- 5. 主迴圈 ---
while True:
    # 獲取當前時間
    now = utime.ticks_ms()

    # --- A. 按鈕處理邏輯 ---
    current_button_state = button.value()

    # 偵測按鈕被按下 (從 0 -> 1)
    if current_button_state == 1 and last_button_state == 0:
        button_press_time = now
        long_press_triggered = False

    # 偵測按鈕被釋放 (從 1 -> 0)
    if current_button_state == 0 and last_button_state == 1:
        press_duration = utime.ticks_diff(now, button_press_time)
        # 如果是短按且未觸發過長按
        if press_duration < SHORT_PRESS_MS and not long_press_triggered:
            is_paused = not is_paused
            if is_paused:
                buzzer_pwm.duty(0) # 暫停時立即關閉蜂鳴器
                print(">> 播放已暫停")
            else:
                # 恢復播放時，將上次事件時間調整為當前時間，以立即播放下一個音符
                last_event_time = now
                # 立即播放當前音符，避免延遲
                if current_note_index < 7: # 如果不是在長停頓狀態
                    scale_name = SCALE_ORDER[current_scale_index]
                    freq = NOTES[scale_name][current_note_index]
                    buzzer_pwm.freq(freq)
                    buzzer_pwm.duty(DUTY_CYCLE)
                print(">> 繼續播放")

    # 偵測按鈕被持續按住
    if current_button_state == 1:
        # 檢查是否達到長按時間，且尚未觸發過長按動作
        if not long_press_triggered and utime.ticks_diff(now, button_press_time) > LONG_PRESS_MS:
            long_press_triggered = True # 標記已觸發，避免重複執行
            # 切換到下一個大調
            current_scale_index = (current_scale_index + 1) % len(SCALE_ORDER)
            # 重置音符到第一個音 (Do)
            current_note_index = 0
            # 更新事件時間，讓新音階立即開始
            last_event_time = now
            # 立即播放新音階的第一個音
            scale_name = SCALE_ORDER[current_scale_index]
            freq = NOTES[scale_name][current_note_index]
            buzzer_pwm.freq(freq)
            # 如果之前是暫停狀態，長按後應開始播放
            if is_paused:
                is_paused = False
            buzzer_pwm.duty(DUTY_CYCLE)

            print(f"!! 長按：切換音階至 {scale_name} 大調")

    # 更新按鈕狀態供下次迴圈比對
    last_button_state = current_button_state


    # --- B. 音樂播放邏輯 ---
    if not is_paused:
        # 根據目前是播音符還是長停頓，決定時間間隔
        interval = PAUSE_DURATION_MS if current_note_index == 7 else NOTE_DURATION_MS

        # 檢查是否已到達下一個事件的時間點
        if utime.ticks_diff(now, last_event_time) >= interval:
            # 更新到下一個音符/狀態
            current_note_index = (current_note_index + 1) % 8 # 7個音符+1個停頓 = 8個狀態

            if current_note_index < 7: # 如果是播放音符 (0-6)
                scale_name = SCALE_ORDER[current_scale_index]
                freq = NOTES[scale_name][current_note_index]
                buzzer_pwm.freq(freq)
                buzzer_pwm.duty(DUTY_CYCLE)
            else: # 如果是音階後的長停頓 (current_note_index == 7)
                buzzer_pwm.duty(0) # 關閉蜂鳴器

            # 更新上次事件的時間戳
            last_event_time = now