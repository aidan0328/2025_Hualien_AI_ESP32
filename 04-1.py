# 實驗 #4-1：讀取並印出可變電阻的類比輸入數值
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC
# 硬體：可變電阻連接至 GPIO36
# 功能：持續讀取 ADC 值並透過序列埠印出，用於序列繪圖器

# 引入必要的模組
from machine import Pin, ADC
import time

# --- 1. 初始化 ADC ---
# 將 GPIO36 設定為 ADC 輸入腳位
# ADC(Pin(36)) 會建立一個與 GPIO36 連接的 ADC 物件
adc_pin = Pin(36)
adc = ADC(adc_pin)

# --- 2. 設定 ADC 的衰減（電壓範圍） ---
# ESP32 的 ADC 需要設定衰減值來決定最大可測量的電壓
# ATTN_11DB 允許測量約 0V ~ 3.3V 的電壓範圍
# 這對於直接連接到 3.3V 和 GND 的可變電阻來說是必要的設定
# 如此一來，0V 對應數位值 0，約 3.3V 對應數位值 4095 (12-bit 解析度)
adc.atten(ADC.ATTN_11DB)

print("ADC 初始化完成，開始讀取數值...")

# --- 3. 進入主迴圈，持續讀取與輸出 ---
try:
    while True:
        # 讀取 ADC 的數位值 (範圍 0-4095)
        adc_value = adc.read()
        
        # 直接印出數值。Arduino 序列繪圖器會自動將每行的數字當作一個資料點
        print(adc_value)
        
        # 延遲 100 毫秒，避免讀取過快導致序列埠壅塞，也讓繪圖器更新更平滑
        # 每秒會讀取 10 次
        time.sleep_ms(100)

except KeyboardInterrupt:
    # 當在 REPL 中按下 Ctrl+C 時，程式會中斷，並印出此訊息
    print("程式已停止。")