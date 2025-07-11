# 實驗 #9-3：蜂鳴器演奏「給愛麗絲」 (非阻塞式 + 播放/暫停功能)

import machine
import utime

# --- 1. 實驗設定 ---
# 腳位設定
BUZZER_PIN = 15
BUTTON_PIN = 23

# 樂曲速度設定 (基礎時長，單位毫秒，數值越小速度越快)
# 代表一個16分音符的長度
BASE_NOTE_DURATION = 125 

# 按鈕防抖動時間 (毫秒)
DEBOUNCE_MS = 50

# --- 2. 音符頻率對照表 (赫茲 Hz) ---
NOTES = {
    '_': 0,     # 休止符 (Rest)
    'B3': 247,
    'C4': 262, 'CS4': 277, 'D4': 294, 'DS4': 311, 'E4': 330, 'F4': 349, 'FS4': 370, 'G4': 392, 'GS4': 415, 'A4': 440, 'AS4': 466, 'B4': 494,
    'C5': 523, 'CS5': 554, 'D5': 587, 'DS5': 622, 'E5': 659, 'F5': 698, 'FS5': 740, 'G5': 784, 'GS5': 831, 'A5': 880, 'AS5': 932, 'B5': 988,
}

# --- 3. 「給愛麗絲」樂譜 ---
# 格式: (音符名稱, 持續時間乘數)
# 乘數 1 = 16分音符, 2 = 8分音符, 3 = 附點8分音符, 4 = 4分音符
FUR_ELISE_SCORE = [
    ('E5', 2), ('DS5', 2), ('E5', 2), ('DS5', 2), ('E5', 2), ('B4', 2), ('D5', 2), ('C5', 2),
    ('A4', 4), ('_', 2), ('C4', 2), ('E4', 2), ('A4', 2), ('B4', 4), ('_', 2), ('E4', 2),
    ('GS4', 2), ('B4', 2), ('C5', 4), ('_', 2), ('E4', 2), ('E5', 2), ('DS5', 2), ('E5', 2),
    ('DS5', 2), ('E5', 2), ('B4', 2), ('D5', 2), ('C5', 2), ('A4', 4), ('_', 2), ('C4', 2),
    ('E4', 2), ('A4', 2), ('B4', 4), ('_', 2), ('E4', 2), ('C5', 2), ('B4', 2), ('A4', 4),
    ('_', 4) # 結尾休止，準備循環
]

# --- 4. 硬體初始化 ---
# 初始化蜂鳴器PWM
# PWM(Pulse Width Modulation)讓我們可以控制頻率來發出不同音高
buzzer_pwm = machine.PWM(machine.Pin(BUZZER_PIN), freq=1000, duty=0)

# 初始化按鈕
# 使用內部下拉電阻，這樣按鈕沒按下時是低電位(0)，按下時(接到3.3V)是高電位(1)
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# --- 5. 狀態變數 ---
# 播放控制
is_playing = True              # 初始狀態為播放
current_note_index = 0         # 當前播放到樂譜的哪個音符

# 時間控制 (非阻塞式核心)
note_start_time = 0            # 當前音符開始播放的時間
pause_start_time = 0           # 進入暫停狀態的開始時間

# 按鈕狀態控制
last_button_state = 0          # 上一次迴圈的按鈕狀態 (用於偵測邊緣觸發)
last_press_time = 0            # 上一次有效按下的時間 (用於防抖動)

# --- 6. 輔助函式 ---
def play_note(freq):
    """根據頻率設定蜂鳴器發聲或靜音"""
    if freq > 0:
        buzzer_pwm.freq(freq) # 設定頻率
        buzzer_pwm.duty(512)  # 設定音量 (0-1023，512約為50%音量)
    else:
        buzzer_pwm.duty(0)    # 靜音

# --- 7. 主迴圈 ---
print("實驗 #9-3：蜂鳴器演奏「給愛麗絲」")
print("短按按鈕可 播放/暫停。")

try:
    # 程式啟動時，立即播放第一個音符
    note_name, _ = FUR_ELISE_SCORE[current_note_index]
    note_freq = NOTES.get(note_name, 0)
    play_note(note_freq)
    note_start_time = utime.ticks_ms()

    while True:
        # 取得當前時間
        now = utime.ticks_ms()
        
        # --- 按鈕狀態偵測 ---
        current_button_state = button.value()
        # 偵測按鈕狀態變化 (從 0->1 或 1->0)
        if current_button_state != last_button_state:
            # 防抖動：確保距離上次有效按下已超過指定時間
            if utime.ticks_diff(now, last_press_time) > DEBOUNCE_MS:
                # 只在按鈕被按下時(從0變1)觸發動作
                if current_button_state == 1:
                    is_playing = not is_playing # 切換播放/暫停狀態
                    
                    if not is_playing:
                        # 進入暫停狀態
                        play_note(0) # 立刻靜音
                        pause_start_time = now # 記錄暫停開始的時間
                        print("Playback Paused.")
                    else:
                        # 恢復播放狀態
                        # 核心技巧：將音符的開始時間往後推移「被暫停的總時間」
                        # 這樣時間差的計算就不會包含暫停的時間
                        time_was_paused = utime.ticks_diff(now, pause_start_time)
                        note_start_time += time_was_paused
                        
                        # 重新播放當前的音符
                        note_name, _ = FUR_ELISE_SCORE[current_note_index]
                        note_freq = NOTES.get(note_name, 0)
                        play_note(note_freq)
                        print("Playback Resumed.")
                        
                    last_press_time = now # 更新最後按下時間
        
        last_button_state = current_button_state

        # --- 音樂播放邏輯 ---
        # 只有在播放狀態下才執行
        if is_playing:
            # 獲取當前音符的資訊
            note_name, duration_multiplier = FUR_ELISE_SCORE[current_note_index]
            note_duration = BASE_NOTE_DURATION * duration_multiplier
            
            # 檢查當前音符的持續時間是否已到
            if utime.ticks_diff(now, note_start_time) >= note_duration:
                # 時間到，前進到下一個音符
                current_note_index += 1
                
                # 如果樂譜播完，從頭開始
                if current_note_index >= len(FUR_ELISE_SCORE):
                    current_note_index = 0
                
                # 獲取下一個音符的頻率並播放
                next_note_name, _ = FUR_ELISE_SCORE[current_note_index]
                next_freq = NOTES.get(next_note_name, 0)
                play_note(next_freq)
                
                # 重設音符開始時間，為下一個音符計時
                note_start_time = now

except KeyboardInterrupt:
    print("程式被手動停止。")
finally:
    # 確保程式結束時關閉蜂鳴器，釋放資源
    buzzer_pwm.deinit()
    print("蜂鳴器已停止，資源已釋放。")