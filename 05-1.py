# 實驗 #5-1：使用可變電阻調整LED的明亮度
# MicroPython v1.24.0 on ESP32-DevKitC

import machine
import time

# --- 硬體腳位定義 ---
# 使用常數來定義腳位，方便管理與修改
ADC_PIN = 36
GREEN_LED_PIN = 21
YELLOW_LED_PIN = 19
RED_LED_PIN = 18

# --- 初始化 Pin 和 ADC 物件 ---
# 初始化 ADC
# GPIO36 是 ADC1 的通道 0
# 設定衰減比為 11dB，這樣才能讀取完整的 0-3.3V 電壓範圍
adc = machine.ADC(machine.Pin(ADC_PIN))
adc.atten(machine.ADC.ATTN_11DB)

# 初始化 LED
# 紅色和黃色 LED 設定為輸出模式並直接關閉
red_led = machine.Pin(RED_LED_PIN, machine.Pin.OUT)
yellow_led = machine.Pin(YELLOW_LED_PIN, machine.Pin.OUT)
red_led.off()
yellow_led.off()

# 綠色 LED 需要 PWM 功能來控制亮度
# 建立 PWM 物件，頻率設定為 1000 Hz 可以避免人眼可見的閃爍
pwm_green = machine.PWM(machine.Pin(GREEN_LED_PIN), freq=1000)


# --- 移動平均 (Moving Average) 相關設定 ---
# 設定要取樣的讀值數量
NUM_READINGS = 10

# 建立一個列表來存放最近的 N 筆讀值
# 初始值全部填 0
readings = [0] * NUM_READINGS

# 用來指向目前要更新的列表位置
reading_index = 0

# 用來存放目前列表內所有讀值的總和
total = 0

print("程式啟動，請旋轉可變電阻來調整綠色LED亮度。")
print("紅色與黃色LED將維持熄滅狀態。")

# --- 主迴圈 ---
while True:
    # 1. 從 readings 列表中減去最舊的一筆資料
    total = total - readings[reading_index]
    
    # 2. 從 ADC 讀取新的值
    # read_u16() 會回傳一個 16-bit 的值 (0-65535)，正好對應 PWM 的 duty_u16()
    # 這比 read() (回傳 0-4095) 更方便，省去了手動轉換的步驟
    new_reading = adc.read_u16()
    
    # 3. 將新的讀值存入列表的當前位置
    readings[reading_index] = new_reading
    
    # 4. 將新的讀值加到總和中
    total = total + new_reading
    
    # 5. 移動索引到下一個位置，準備下次覆寫
    # 使用取餘數 (%) 運算子實現環狀佇列的效果
    reading_index = (reading_index + 1) % NUM_READINGS
    
    # 6. 計算移動平均值
    # 使用整數除法 (//) 即可
    average_adc = total // NUM_READINGS
    
    # 7. 將平滑處理後的平均值設定為 PWM 的 duty cycle
    # 因為我們使用了 read_u16()，其範圍 (0-65535) 完美對應 duty_u16()
    # 當可變電阻轉到底 (0V)，average_adc 接近 0，LED 熄滅
    # 當可變電阻轉到頂 (3.3V)，average_adc 接近 65535，LED 最亮
    pwm_green.duty_u16(average_adc)

    # 8. (可選) 在 REPL 印出目前讀值，方便除錯和觀察
    # 使用字串串接來避免 f-string
    print("原始ADC讀值: ", str(new_reading), " , 平滑後平均值 (Duty): ", str(average_adc))
    
    # 9. 短暫延遲，決定更新頻率
    # 50ms 的延遲讓系統有足夠的反應時間，同時不會過度佔用 CPU
    time.sleep_ms(50)