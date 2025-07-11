# 實驗 #6-2：按鈕短按切換 LED 模式、長按關閉所有 LED (修正版)
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import asyncio
import time
import math
from collections import deque

# --- 硬體與常數設定 ---

# LED 接腳
PIN_LED_R = 18
PIN_LED_Y = 19
PIN_LED_G = 21

# ADC (可變電阻) 接腳
PIN_ADC = 36

# 按鈕接腳
PIN_BUTTON = 23

# 按鍵偵測時間 (ms)
DEBOUNCE_MS = 50
LONG_PRESS_MS = 1000

# LED 模式定義
MODE_KNIGHT_RIDER = 0
MODE_BREATHING = 1
MODE_ALL_ON = 2
NUM_MODES = 3

# ADC 範圍 (ESP32 ADC 為 12-bit)
ADC_MIN = 0
ADC_MAX = 4095

# --- 應用程式狀態管理 ---

class AppState:
    def __init__(self):
        self.mode = MODE_KNIGHT_RIDER
        self.leds_off = False
        self.adc_value = 0
        self.current_pattern_task = None
        self.adc_samples = deque((), 10) # 10筆移動平均的樣本
        self.press_duration = 0 # 用於儲存按鍵時長

app_state = AppState()

# --- 事件定義 (簡化為單一事件) ---
button_event = asyncio.Event()


# --- 工具函式 ---

def map_value(x, in_min, in_max, out_min, out_max):
    """將一個值從一個範圍線性對應到另一個範圍"""
    if x < in_min: x = in_min
    if x > in_max: x = in_max
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# --- 非同步任務 (Async Tasks) ---

async def button_handler(pin):
    """非阻塞式按鍵處理任務，偵測短按與長按"""
    last_state = pin.value()
    while True:
        current_state = pin.value()
        if current_state == 1 and last_state == 0:
            # 按鍵按下
            press_time = time.ticks_ms()
            await asyncio.sleep_ms(DEBOUNCE_MS) # 去抖動
            
            # 等待按鍵放開
            while pin.value() == 1:
                await asyncio.sleep_ms(50)
            
            release_time = time.ticks_ms()
            
            # 儲存按鍵時長並觸發事件
            app_state.press_duration = time.ticks_diff(release_time, press_time)
            if app_state.press_duration >= DEBOUNCE_MS:
                button_event.set()
        
        last_state = current_state
        await asyncio.sleep_ms(20)

async def adc_handler(pin):
    """非阻塞式 ADC 讀取任務，並進行移動平均濾波"""
    adc = machine.ADC(pin)
    adc.atten(machine.ADC.ATTN_11DB)
    
    while True:
        current_reading = adc.read()
        app_state.adc_samples.append(current_reading)
        app_state.adc_value = sum(app_state.adc_samples) // len(app_state.adc_samples)
        await asyncio.sleep_ms(50)

async def pattern_knight_rider(leds, period_min=500, period_max=3000):
    """模式 A: 左右來回跑馬燈"""
    pattern = [0, 1, 2, 1]
    try:
        while True:
            period_ms = map_value(app_state.adc_value, ADC_MIN, ADC_MAX, period_min, period_max)
            delay_ms = int(period_ms / len(pattern))
            print(f"跑馬燈模式 - 週期: {period_ms / 1000:.2f}s")

            for i in pattern:
                for j, led in enumerate(leds):
                    led.duty(1023 if i == j else 0)
                await asyncio.sleep_ms(delay_ms)
    except asyncio.CancelledError:
        print("跑馬燈模式取消")

async def pattern_breathing_lights(leds, period_min=500, period_max=3000):
    """模式 B: 三顆 LED 同步呼吸燈"""
    try:
        i = 0
        while True:
            period_ms = map_value(app_state.adc_value, ADC_MIN, ADC_MAX, period_min, period_max)
            delay_ms = int(period_ms / 120)
            print(f"呼吸燈模式 - 週期: {period_ms / 1000:.2f}s")
            
            brightness = (math.sin(i * math.pi / 60) + 1) / 2
            duty = int(brightness * 1023)
            
            for led in leds:
                led.duty(duty)
            
            i = (i + 1) % 120
            await asyncio.sleep_ms(delay_ms)
    except asyncio.CancelledError:
        print("呼吸燈模式取消")

async def pattern_all_on(leds):
    """模式 C: 三顆 LED 恆亮，由 ADC 控制亮度"""
    try:
        while True:
            brightness = int(map_value(app_state.adc_value, ADC_MIN, ADC_MAX, 0, 1023))
            print(f"恆亮模式 - 亮度: {brightness}")
            for led in leds:
                led.duty(brightness)
            await asyncio.sleep_ms(50)
    except asyncio.CancelledError:
        print("恆亮模式取消")

async def led_manager(leds):
    """主 LED 管理任務，根據事件與狀態切換模式"""
    patterns = {
        MODE_KNIGHT_RIDER: pattern_knight_rider,
        MODE_BREATHING: pattern_breathing_lights,
        MODE_ALL_ON: pattern_all_on,
    }
    
    while True:
        # 取消之前的模式任務
        if app_state.current_pattern_task:
            app_state.current_pattern_task.cancel()
            await asyncio.sleep_ms(0)
            app_state.current_pattern_task = None
        
        # 檢查是否為關燈狀態
        if app_state.leds_off:
            for led in leds:
                led.duty(0)
            print("所有 LED 已關閉")
            await button_event.wait()
            button_event.clear()
            # 只有長按能喚醒，但我們在這裡再次檢查以確保
            if app_state.press_duration >= LONG_PRESS_MS:
                app_state.leds_off = False
                app_state.mode = MODE_KNIGHT_RIDER
                print("從關閉狀態喚醒，重置為模式 A")
            continue # 重新進入主循環來處理新模式

        # 啟動新模式的任務
        pattern_func = patterns.get(app_state.mode)
        if pattern_func:
            print(f"切換至模式: {pattern_func.__name__}")
            app_state.current_pattern_task = asyncio.create_task(pattern_func(leds))

        # 等待按鍵事件
        await button_event.wait()
        button_event.clear()
            
        # 處理事件
        if app_state.press_duration >= LONG_PRESS_MS:
            print("偵測到長按")
            app_state.leds_off = True
        else:
            print("偵測到短按")
            app_state.mode = (app_state.mode + 1) % NUM_MODES

async def main():
    """主程式進入點，初始化硬體並啟動所有非同步任務"""
    button = machine.Pin(PIN_BUTTON, machine.Pin.IN, machine.Pin.PULL_DOWN)
    adc_pin = machine.Pin(PIN_ADC)
    
    leds = [
        machine.PWM(machine.Pin(PIN_LED_R), freq=1000),
        machine.PWM(machine.Pin(PIN_LED_Y), freq=1000),
        machine.PWM(machine.Pin(PIN_LED_G), freq=1000),
    ]

    print("啟動按鍵與 ADC 偵測...")
    asyncio.create_task(button_handler(button))
    asyncio.create_task(adc_handler(adc_pin))
    
    print("啟動 LED 管理器...")
    await led_manager(leds)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程式被手動中斷")
    finally:
        asyncio.new_event_loop()
        print("程式結束，重置事件循環")