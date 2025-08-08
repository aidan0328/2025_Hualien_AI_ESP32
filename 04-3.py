# 實驗 #4-3：進階平滑技術來取得可變電阻的 ADC 類比輸入值
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC
# 硬體接線：可變電阻中間接腳 -> GPIO36

import machine
import time
from collections import deque

# --- 1. 常數與設定 ---
ADC_PIN = 36              # 可變電阻連接的 ADC 接腳 (GPIO36 是 ADC1_CHANNEL_0)
SAMPLES_TECH_1 = 10       # 技術1的取樣筆數
WINDOW_SIZE_TECH_2 = 10   # 技術2 (移動平均) 的視窗大小
LOOP_DELAY_MS = 50        # 主迴圈每次讀取的延遲時間 (毫秒)

# --- 2. 硬體初始化 ---
# 設定 ADC
# - Pin(ADC_PIN): 指定接腳
# - atten=machine.ADC.ATTN_11DB: 設定衰減，讓 ADC 可以測量 0V 到 3.3V 的電壓
#   這會將電壓範圍對應到 0-4095 的數位值
# - width=machine.ADC.WIDTH_12BIT: 設定解析度為 12-bit (0-4095)
try:
    adc = machine.ADC(machine.Pin(ADC_PIN))
    adc.atten(machine.ADC.ATTN_11DB)
    adc.width(machine.ADC.WIDTH_12BIT)
    print("ADC on GPIO36 initialized successfully.")
except Exception as e:
    print(f"Error initializing ADC: {e}")
    # 如果 ADC 初始化失敗，就停止程式
    while True:
        time.sleep(1)

# --- 3. 平滑技術函式與類別 ---

# 技術1：排除最大最小值後取平均 (Trimmed Mean)
def get_trimmed_mean_adc(adc_instance, num_samples):
    """
    連續讀取指定數量的 ADC 值，去除一個最大值和一個最小值，
    然後計算剩餘值的平均值。
    """
    readings = []
    for _ in range(num_samples):
        readings.append(adc_instance.read())
        time.sleep_ms(1)  # 每次 ADC 讀取之間短暫延遲，讓 ADC 穩定

    if len(readings) < 3:
        # 如果樣本數不足3，無法去除最大最小值，直接回傳平均
        return sum(readings) // len(readings) if readings else 0

    readings.sort()  # 將讀取到的值排序
    
    # 排除第一個 (最小值) 和最後一個 (最大值)
    trimmed_list = readings[1:-1]
    
    # 計算剩下值的總和並取平均
    average = sum(trimmed_list) // len(trimmed_list)
    return average

# 技術2：移動平均 (Moving Average)
# 使用類別來儲存歷史資料，這樣更清晰且易於管理
class MovingAverage:
    """
    一個簡單的移動平均濾波器類別。
    """
    def __init__(self, window_size):
        # 使用 deque 是一個高效的選擇，因為從左邊移除元素 (popleft) 的時間複雜度是 O(1)
        self.data = deque((), window_size)
        self.window_size = window_size

    def add(self, new_value):
        """新增一個值到資料視窗中"""
        self.data.append(new_value)

    def get_average(self):
        """計算目前視窗內所有值的平均值"""
        if not self.data:
            return 0  # 避免除以零的錯誤
        
        # 回傳整數平均值
        return sum(self.data) // len(self.data)

# --- 4. 主程式 ---

# 建立一個移動平均濾波器的實例
ma_filter = MovingAverage(WINDOW_SIZE_TECH_2)

# 為了讓移動平均的初始值更穩定，可以先"預填"資料
print("Priming moving average filter...")
for _ in range(WINDOW_SIZE_TECH_2):
    initial_val = adc.read()
    ma_filter.add(initial_val)
    time.sleep_ms(5)
print("Priming complete. Starting main loop.")

# 為了讓序列繪圖器知道各條線的名稱，先印出標頭
print("Raw,TrimmedMean,MovingAverage")

while True:
    try:
        # 取得「原始值」
        # 注意：為了讓移動平均能持續更新，我們將原始值直接加入移動平均濾波器
        raw_value = adc.read()
        ma_filter.add(raw_value)

        # 取得「第1種平滑值」
        # 每次都重新取樣計算
        trimmed_mean_value = get_trimmed_mean_adc(adc, SAMPLES_TECH_1)
        
        # 取得「第2種平滑值」
        moving_average_value = ma_filter.get_average()

        # 輸出成 Arduino 序列繪圖器可讀的格式 (值之間用逗號分隔)
        print(f"{raw_value},{trimmed_mean_value},{moving_average_value}")
        
        # 延遲一段時間，避免洗版，也讓繪圖器有時間更新
        time.sleep_ms(LOOP_DELAY_MS)

    except KeyboardInterrupt:
        print("Program stopped by user.")
        break
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(1) # 發生錯誤時暫停一下