# ----------------------------------------------------------------------
# 實驗 #20-3-1：ESP32 雙向 ESP-NOW 控制 (ESP32 #1)
# ----------------------------------------------------------------------
import network
import espnow
from machine import Pin
import time
import ubinascii

# --- 硬體與網路設定 ---

# 硬體腳位定義
led_pin = Pin(2, Pin.OUT, value=0)  # 內建 LED 在 GPIO2，初始關閉
# 按鈕在 GPIO23，使用內部上拉電阻，按下時為低電位
button_pin = Pin(23, Pin.IN, Pin.PULL_UP)

# MAC 地址定義
mac_esp1_str = "F4:65:0B:AD:99:A0"
mac_esp2_str = "D8:13:2A:7A:72:98"

# 將字串格式的 MAC 地址轉換為 ESP-NOW 需要的位元組格式
# 對方 (Peer) 的 MAC 地址
peer_mac_bytes = ubinascii.unhexlify(mac_esp2_str.replace(':', ''))


# --- 初始化 ESP-NOW ---

print("實驗 #20-3-1: ESP32 #1 啟動中...")

# 1. 初始化 Wi-Fi STA 模式
# ESP-NOW 需要 Wi-Fi 處於活動狀態，但不需要連接到任何 AP
sta = network.WLAN(network.STA_IF)
sta.active(True)

# 2. 初始化 ESP-NOW
e = espnow.ESPNow()
e.active(True)

# 3. 新增對方為 Peer
try:
    e.add_peer(peer_mac_bytes)
    print("成功新增 Peer: ", mac_esp2_str)
except OSError as e:
    print("新增 Peer 失敗: ", e)


# 4. 顯示本機與對方的 MAC 地址 (符合要求 0-4)
my_mac_bytes = sta.config('mac')
my_mac_str = ubinascii.hexlify(my_mac_bytes, ':').decode().upper()

print("--- 初始化完成 ---")
print("本機 (ESP32 #1) MAC 地址: ", my_mac_str)
print("對方 (ESP32 #2) MAC 地址: ", mac_esp2_str)
print("--------------------")


# --- 中斷處理函式與主迴圈 ---

# 建立一個旗標來表示按鈕是否被按下，避免在 ISR 中執行複雜操作
button_pressed_flag = False
last_press_time = 0 # 用於按鈕防抖動

def button_irq_handler(pin):
    """按鈕中斷服務常式 (ISR)"""
    global button_pressed_flag, last_press_time
    # 簡單的防抖動處理 (debounce)
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_press_time) > 200: # 200毫秒的防抖間隔
        button_pressed_flag = True
        last_press_time = current_time

# 設定中斷，當按鈕被按下 (電位從高變低) 時觸發
button_pin.irq(trigger=Pin.IRQ_FALLING, handler=button_irq_handler)

print("系統準備就緒，可以開始互相控制...")

# 主迴圈
while True:
    # 檢查是否需要發送訊息 (由中斷旗標觸發)
    if button_pressed_flag:
        print("偵測到按鈕按下，發送訊息給 ESP32 #2...")
        try:
            # 發送一個簡單的位元組訊息，內容可以是任何東西
            e.send(peer_mac_bytes, b'toggle_led')
        except OSError as err:
            print("發送訊息失敗: ", err)
        
        button_pressed_flag = False # 處理完畢後，重置旗標

    # 檢查是否接收到訊息 (非阻塞模式)
    host, msg = e.recv(0) # 設置 timeout=0 為非阻塞
    if msg: # 如果收到了訊息
        # 將收到的 MAC 位元組轉換為字串以供顯示
        sender_mac = ubinascii.hexlify(host, ':').decode().upper()
        print("從 ", sender_mac, " 收到訊息: ", msg.decode())
        
        # 切換本機 LED 狀態 (符合要求 0-0，不使用 toggle())
        current_led_state = led_pin.value()
        led_pin.value(not current_led_state)
        print("切換本機 LED 狀態為: ", "開" if not current_led_state else "關")

    # 短暫延遲，降低 CPU 使用率
    time.sleep_ms(20)