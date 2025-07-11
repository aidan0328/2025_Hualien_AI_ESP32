# -*- coding: utf-8 -*-

"""
用於透過 I2C 控制 HD44780 相容字元 LCD 的整合驅動程式。

此檔案整合了 lcd_api.py (通用 API 邏輯) 和 machine_i2c_lcd.py (基於 MicroPython I2C 的硬體實作)。
主要使用的類別是 I2cLcd。

範例用法請參見檔案結尾的 `if __name__ == "__main__":` 區塊。
"""

import time

# =============================================================================
# START OF LcdApi (來自 lcd_api.py)
# =============================================================================

class LcdApi:
    """
    實作與 HD44780 相容字元 LCD 通訊的 API。
    這個類別只知道要發送什麼指令給 LCD，但不知道如何將它們傳送到 LCD。

    它期望派生類別 (derived class) 會實作 hal_xxx 函式。
    """

    # 下列常數名稱取自 avrlib lcd.h 標頭檔，
    # 但定義從位元編號改為位元遮罩。
    #
    # HD44780 LCD 控制器指令集

    LCD_CLR = 0x01              # DB0: 清除顯示
    LCD_HOME = 0x02             # DB1: 回到起始位置

    LCD_ENTRY_MODE = 0x04       # DB2: 設定輸入模式
    LCD_ENTRY_INC = 0x02        # --DB1: 位址遞增
    LCD_ENTRY_SHIFT = 0x01      # --DB0: 畫面平移

    LCD_ON_CTRL = 0x08          # DB3: 開啟/關閉 LCD/游標
    LCD_ON_DISPLAY = 0x04       # --DB2: 開啟顯示
    LCD_ON_CURSOR = 0x02        # --DB1: 開啟游標
    LCD_ON_BLINK = 0x01         # --DB0: 游標閃爍

    LCD_MOVE = 0x10             # DB4: 移動游標/顯示
    LCD_MOVE_DISP = 0x08        # --DB3: 移動顯示 (0-> 移動游標)
    LCD_MOVE_RIGHT = 0x04       # --DB2: 向右移動 (0-> 向左)

    LCD_FUNCTION = 0x20         # DB5: 功能設定
    LCD_FUNCTION_8BIT = 0x10    # --DB4: 設定 8 位元模式 (0->4 位元模式)
    LCD_FUNCTION_2LINES = 0x08  # --DB3: 雙行 (0->單行)
    LCD_FUNCTION_10DOTS = 0x04  # --DB2: 5x10 字型 (0->5x7 字型)
    LCD_FUNCTION_RESET = 0x30   # 請參閱 "Initializing by Instruction" 章節

    LCD_CGRAM = 0x40            # DB6: 設定 CG RAM 位址
    LCD_DDRAM = 0x80            # DB7: 設定 DD RAM 位址

    LCD_RS_CMD = 0
    LCD_RS_DATA = 1

    LCD_RW_WRITE = 0
    LCD_RW_READ = 1

    def __init__(self, num_lines, num_columns):
        self.num_lines = num_lines
        if self.num_lines > 4:
            self.num_lines = 4
        self.num_columns = num_columns
        if self.num_columns > 40:
            self.num_columns = 40
        self.cursor_x = 0
        self.cursor_y = 0
        self.implied_newline = False
        self.backlight = True
        self.display_off()
        self.backlight_on()
        self.clear()
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)
        self.hide_cursor()
        self.display_on()

    def clear(self):
        """清除 LCD 顯示並將游標移至左上角。"""
        self.hal_write_command(self.LCD_CLR)
        self.hal_write_command(self.LCD_HOME)
        self.cursor_x = 0
        self.cursor_y = 0

    def show_cursor(self):
        """讓游標可見。"""
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                               self.LCD_ON_CURSOR)

    def hide_cursor(self):
        """隱藏游標。"""
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def blink_cursor_on(self):
        """開啟游標並使其閃爍。"""
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                               self.LCD_ON_CURSOR | self.LCD_ON_BLINK)

    def blink_cursor_off(self):
        """開啟游標並使其不閃爍 (即實心)。"""
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                               self.LCD_ON_CURSOR)

    def display_on(self):
        """開啟 (即取消空白) LCD。"""
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def display_off(self):
        """關閉 (即空白) LCD。"""
        self.hal_write_command(self.LCD_ON_CTRL)

    def backlight_on(self):
        """開啟背光。"""
        self.backlight = True
        self.hal_backlight_on()

    def backlight_off(self):
        """關閉背光。"""
        self.backlight = False
        self.hal_backlight_off()

    def move_to(self, cursor_x, cursor_y):
        """將游標位置移動到指定位置。游標位置是從零開始的。"""
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        addr = cursor_x & 0x3f
        if cursor_y & 1:
            addr += 0x40    # 第 1 和 3 行位址加 0x40
        if cursor_y & 2:    # 第 2 和 3 行位址加欄數
            addr += self.num_columns
        self.hal_write_command(self.LCD_DDRAM | addr)

    def putchar(self, char):
        """將指定字元寫入 LCD 目前游標位置，並將游標前進一格。"""
        if char == '\n':
            if self.implied_newline:
                self.implied_newline = False
            else:
                self.cursor_x = self.num_columns
        else:
            self.hal_write_data(ord(char))
            self.cursor_x += 1
        if self.cursor_x >= self.num_columns:
            self.cursor_x = 0
            self.cursor_y += 1
            self.implied_newline = (char != '\n')
        if self.cursor_y >= self.num_lines:
            self.cursor_y = 0
        self.move_to(self.cursor_x, self.cursor_y)

    def putstr(self, string):
        """將指定字串寫入 LCD 目前游標位置。"""
        for char in string:
            self.putchar(char)

    def custom_char(self, location, charmap):
        """將自訂字元寫入 8 個 CGRAM 位置之一 (可透過 chr(0) 到 chr(7) 使用)。"""
        location &= 0x7
        self.hal_write_command(self.LCD_CGRAM | (location << 3))
        self.hal_sleep_us(40)
        for i in range(8):
            self.hal_write_data(charmap[i])
            self.hal_sleep_us(40)
        self.move_to(self.cursor_x, self.cursor_y)

    def hal_backlight_on(self):
        """允許 HAL 層開啟背光。如果需要，派生類別將實作此函式。"""
        pass

    def hal_backlight_off(self):
        """允許 HAL 層關閉背光。如果需要，派生類別將實作此函式。"""
        pass

    def hal_write_command(self, cmd):
        """向 LCD 寫入指令。期望派生類別實作此函式。"""
        raise NotImplementedError

    def hal_write_data(self, data):
        """向 LCD 寫入資料。期望派生類別實作此函式。"""
        raise NotImplementedError

    def hal_sleep_us(self, usecs):
        """延遲指定時間 (微秒)。
        這是適用於大多數 micropython 實作的預設方法。
        """
        time.sleep_us(usecs)

# =============================================================================
# END OF LcdApi
# =============================================================================


# =============================================================================
# START OF I2cLcd (來自 machine_i2c_lcd.py)
# =============================================================================

# PCF8574 的 I2C 位址可透過跳線選擇：0x20 - 0x27
DEFAULT_I2C_ADDR = 0x27

# PCF8574 上連接 LCD 線路的移位或遮罩定義
MASK_RS = 0x01
MASK_RW = 0x02
MASK_E = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4


class I2cLcd(LcdApi):
    """實作透過 I2C 上的 PCF8574 連接的 HD44780 字元 LCD。"""

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.i2c.writeto(self.i2c_addr, bytearray([0]))
        time.sleep_ms(20)   # 讓 LCD 有時間上電
        # 發送重置指令 3 次
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        time.sleep_ms(5)    # 需要延遲至少 4.1 毫秒
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        time.sleep_ms(1)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        time.sleep_ms(1)
        # 將 LCD 設定為 4 位元模式
        self.hal_write_init_nibble(self.LCD_FUNCTION)
        time.sleep_ms(1)
        super().__init__(num_lines, num_columns)
        cmd = self.LCD_FUNCTION
        if num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)

    def hal_write_init_nibble(self, nibble):
        """向 LCD 寫入一個初始化半位元組 (nibble)。此函式僅在初始化期間使用。"""
        byte = ((nibble >> 4) & 0x0f) << SHIFT_DATA
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))

    def hal_backlight_on(self):
        """開啟背光。"""
        self.i2c.writeto(self.i2c_addr, bytearray([1 << SHIFT_BACKLIGHT]))

    def hal_backlight_off(self):
        """關閉背光。"""
        self.i2c.writeto(self.i2c_addr, bytearray([0]))

    def hal_write_command(self, cmd):
        """向 LCD 寫入指令。資料在 E 的下降沿被鎖存。"""
        # 發送高 4 位元
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                (((cmd >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))
        # 發送低 4 位元
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                ((cmd & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))
        # home 和 clear 指令需要較長的延遲
        if cmd <= 3:
            time.sleep_ms(5)

    def hal_write_data(self, data):
        """向 LCD 寫入資料。"""
        # 發送高 4 位元
        byte = (MASK_RS | (self.backlight << SHIFT_BACKLIGHT) |
                (((data >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))
        # 發送低 4 位元
        byte = (MASK_RS | (self.backlight << SHIFT_BACKLIGHT) |
                ((data & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))

# =============================================================================
# END OF I2cLcd
# =============================================================================
