# 實驗 #13-1： 8x8 LED點矩陣顯示模組顯示數字 (非阻塞式)
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

import machine
import time

# --- MAX7219 硬體設定 ---
# 根據您的接線修改
SCK_PIN = 26  # CLK
MOSI_PIN = 33 # DIN
CS_PIN = 25   # CS

# --- 8x8 點矩陣字型資料 (數字 0-9) ---
# 每個數字由 8 個 byte 組成，每個 byte 代表矩陣的一列 (row)
# 可以在 https://xantorohara.github.io/led-matrix-editor/ 編輯器中自行設計
DIGITS = [
  bytearray([0x3c, 0x42, 0x42, 0x42, 0x42, 0x42, 0x3c, 0x00]),  # 0
  bytearray([0x08, 0x18, 0x08, 0x08, 0x08, 0x08, 0x1c, 0x00]),  # 1
  bytearray([0x3c, 0x02, 0x02, 0x3c, 0x20, 0x20, 0x3e, 0x00]),  # 2
  bytearray([0x3c, 0x02, 0x02, 0x1c, 0x02, 0x02, 0x3c, 0x00]),  # 3
  bytearray([0x04, 0x0c, 0x14, 0x24, 0x7e, 0x04, 0x04, 0x00]),  # 4
  bytearray([0x3e, 0x20, 0x20, 0x3c, 0x02, 0x02, 0x3c, 0x00]),  # 5
  bytearray([0x3c, 0x20, 0x20, 0x3c, 0x22, 0x22, 0x3c, 0x00]),  # 6
  bytearray([0x3e, 0x02, 0x04, 0x08, 0x10, 0x10, 0x10, 0x00]),  # 7
  bytearray([0x3c, 0x22, 0x22, 0x3c, 0x22, 0x22, 0x3c, 0x00]),  # 8
  bytearray([0x3c, 0x22, 0x22, 0x3e, 0x02, 0x02, 0x3c, 0x00])   # 9
]


class Matrix8x8:
    """
    一個簡單的 MAX7219 8x8 LED 點矩陣驅動類別
    """
    # MAX7219 指令集
    _NOOP = 0x00
    _DIGIT0 = 0x01
    _DECODE_MODE = 0x09
    _INTENSITY = 0x0A
    _SCAN_LIMIT = 0x0B
    _SHUTDOWN = 0x0C
    _DISPLAY_TEST = 0x0F

    def __init__(self, spi, cs):
        """
        初始化函式
        :param spi: machine.SPI 物件
        :param cs: machine.Pin 物件 (Chip Select)
        """
        self.spi = spi
        self.cs = cs
        self.cs.init(self.cs.OUT, True)  # 初始化 CS 腳位為輸出，並設為高電位
        self.init_display()

    def _write(self, command, data):
        """
        透過 SPI 傳送指令和資料到 MAX7219
        """
        self.cs(0)  # 致能晶片 (CS low)
        self.spi.write(bytearray([command, data]))
        self.cs(1)  # 禁能晶片 (CS high)

    def init_display(self):
        """
        初始化 MAX7219 晶片設定
        """
        self._write(self._DECODE_MODE, 0x00)     # 設定為非解碼模式
        self._write(self._SCAN_LIMIT, 0x07)      # 掃描限制：掃描所有8行
        self._write(self._INTENSITY, 0x07)       # 設定亮度 (0x00-0x0F)
        self._write(self._SHUTDOWN, 0x01)        # 進入正常運作模式 (從休眠喚醒)
        self._write(self._DISPLAY_TEST, 0x00)    # 關閉測試模式
        self.clear()                             # 清空螢幕

    def brightness(self, value):
        """
        設定螢幕亮度
        :param value: 亮度值 0 到 15
        """
        if 0 <= value <= 15:
            self._write(self._INTENSITY, value)

    def clear(self):
        """
        清除螢幕所有 LED
        """
        for i in range(8):
            self._write(self._DIGIT0 + i, 0x00)

    def show_char(self, char_data):
        """
        在矩陣上顯示一個字元圖案
        :param char_data: 一個包含8個 byte 的 bytearray
        """
        for i in range(8):
            # DIGIT0(0x01) 到 DIGIT7(0x08) 對應矩陣的 row 1 到 row 8
            self._write(self._DIGIT0 + i, char_data[i])


# --- 主程式 ---
def main():
    # 1. 初始化 SPI
    # ESP32 的 SPI(1) 預設腳位為 SCK=14, MOSI=13, MISO=12
    # 這裡我們使用自訂腳位，因此需要明確指定
    spi = machine.SPI(1, baudrate=10000000, polarity=0, phase=0,
                      sck=machine.Pin(SCK_PIN),
                      mosi=machine.Pin(MOSI_PIN))
    
    cs = machine.Pin(CS_PIN, machine.Pin.OUT)

    # 2. 建立 Matrix8x8 物件
    display = Matrix8x8(spi, cs)
    print("8x8 LED 點矩陣模組初始化完成。")

    # 3. 非阻塞式迴圈變數設定
    interval_ms = 1000  # 每個數字顯示 1000 毫秒 (1秒)
    last_update_time = time.ticks_ms()  # 記錄上次更新時間
    current_digit_index = 0

    # 4. 程式啟動時，先顯示第一個數字 (0)
    print(f"顯示數字: {current_digit_index}")
    display.show_char(DIGITS[current_digit_index])

    # 5. 主迴圈 (非阻塞式)
    while True:
        # 獲取當前時間
        current_time = time.ticks_ms()

        # 檢查距離上次更新是否已超過指定間隔
        # time.ticks_diff() 用於處理計時器溢位問題，比直接相減更安全
        if time.ticks_diff(current_time, last_update_time) >= interval_ms:
            # 更新時間戳
            last_update_time = current_time

            # 計算下一個要顯示的數字索引 (0-9 循環)
            current_digit_index = (current_digit_index + 1) % 10

            # 在矩陣上顯示新的數字
            print(f"顯示數字: {current_digit_index}")
            display.show_char(DIGITS[current_digit_index])
        
        # 在這裡可以執行其他非阻塞的任務，整個程式不會被卡住
        # 例如：檢查按鈕、讀取感測器等
        # time.sleep_ms(10) # 可以加入短暫延遲，降低 CPU 使用率，但非必要

# --- 執行主程式 ---
if __name__ == "__main__":
    main()