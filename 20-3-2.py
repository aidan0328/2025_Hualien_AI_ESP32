# ----------------------------------------------------------------------
# 實驗 #20-3-2：ESP32 雙向 ESP-NOW 控制 (ESP32 #2)
# ----------------------------------------------------------------------
import network
import espnow
import machine
import time
import ubinascii

# --- 硬體與常數設定 ---
LED_PIN = 2
BUTTON_PIN = 23
DEBOUNCE_MS = 200 # 按鈕防抖動的毫秒數

# ----------------------------------------------------------------------
# !!! 重要設定：請根據您正在設定的開發板來選擇對應的 MAC 位址 !!!
# ----------------------------------------------------------------------

# ▼▼▼ 設定為【ESP32 #1】時使用此區塊 ▼▼▼
# MY_BOARD_NAME = "ESP32 #1"
# MY_MAC_STR = "F4:65:0B:AD:99:A0"
# PEER_MAC_STR = "5C:01:3B:E3:7B:08"
# ▲▲▲ 設定為【ESP32 #1】時使用此區塊 ▲▲▲

# ▼▼▼ 設定為【ESP32 #2】時，請註解上面區塊，並取消註解此區塊 ▼▼▼
MY_BOARD_NAME = "ESP32 #2"
MY_MAC_STR = "5C:01:3B:E3:7B:08"
PEER_MAC_STR = "F4:65:0B:AD:99:A0"
# ▲▲▲ 設定為【ESP32 #2】時使用此區塊 ▲▲▲

# ----------------------------------------------------------------------

# 全域變數
last_press_time = 0
led = machine.Pin(LED_PIN, machine.Pin.OUT)

# 輔助函式：切換 LED 狀態
def toggle_led(p):
    p.value(not p.value())

# 中斷服務常式 (ISR)，當按鈕被按下時觸發
def button_isr(pin):
    global last_press_time
    now = time.ticks_ms()
    # 簡易的防抖動處理
    if time.ticks_diff(now, last_press_time) > DEBOUNCE_MS:
        last_press_time = now
        print("按鈕被按下，傳送 'toggle' 訊息...")
        try:
            e.send(PEER_MAC_BIN, b'toggle')
        except OSError as err:
            print("傳送失敗: {}".format(err))

# --- 主程式開始 ---

# 1. 初始化WLAN Station介面 (ESP-NOW的必要條件)
sta = network.WLAN(network.STA_IF)
sta.active(True)
# ESP8266需要disconnect，ESP32通常不需要，但保留也無害
if hasattr(sta, 'disconnect'):
    sta.disconnect()

# 2. 初始化ESP-NOW
e = espnow.ESPNow()
e.active(True)

# 3. 處理MAC位址
# 將字串格式的MAC位址轉換為ESP-NOW需要的二進位格式
MY_MAC_BIN = ubinascii.unhexlify(MY_MAC_STR.replace(':', ''))
PEER_MAC_BIN = ubinascii.unhexlify(PEER_MAC_STR.replace(':', ''))

# 4. 新增對方位址到 ESP-NOW 列表中
try:
    e.add_peer(PEER_MAC_BIN)
except OSError as e:
    # 如果對方已經存在，可能會引發 OSError，這裡我們忽略它
    if "ESP_ERR_ESPNOW_EXIST" not in str(e):
        raise

# 5. 顯示初始化資訊
print("--- ESP-NOW 雙向控制器 ---")
print("初始化完成: {}".format(MY_BOARD_NAME))
print("本機 MAC 位址: {}".format(MY_MAC_STR))
print("對方位址: {}".format(PEER_MAC_STR))

# 6. 設定硬體 (LED 和 按鈕)
led.off() # 確保啟動時LED是熄滅的
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# 7. 設定按鈕中斷
button.irq(trigger=machine.Pin.IRQ_RISING, handler=button_isr)

# 8. 進入主迴圈，等待接收訊息
print("\n系統準備就緒，等待按鈕觸發或接收訊息...")
while True:
    host, msg = e.recv()
    if msg:
        # 將接收到的MAC位址轉為可讀格式
        host_str = ubinascii.hexlify(host, ':').decode()
        print("從 {} 收到訊息: {}".format(host_str, msg))

        # 如果收到 'toggle' 指令，就切換本機LED
        if msg == b'toggle':
            print("指令正確，切換本機 LED 狀態")
            toggle_led(led)
