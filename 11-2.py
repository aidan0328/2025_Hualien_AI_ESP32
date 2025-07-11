# 實驗 #11-2 (修正版)：具有溫濕度顯示的非阻塞式電子時鐘
# 執行環境：MicroPython v1.24.0 on ESP32-DevKitC

from machine import Pin, I2C, RTC
import time
import dht
import network
import ntptime
import LCD1602 # 匯入您提供的 LCD 驅動程式

# --- 使用者設定 ---
# 請在此處填寫您的 Wi-Fi 資訊
WIFI_SSID = "Hi-NET" 
WIFI_PASSWORD = "09760233690"

# --- 硬體與常數設定 ---
I2C_SCL_PIN = 17
I2C_SDA_PIN = 16
DHT_DATA_PIN = 5

# 時間相關設定
UTC_OFFSET = 8 

# 非阻塞式迴圈的更新間隔 (毫秒)
DISPLAY_UPDATE_INTERVAL_MS = 1000
SENSOR_READ_INTERVAL_MS = 2000
NTP_SYNC_INTERVAL_MS = 5 * 60 * 1000

# --- Wi-Fi 連線函式 ---
def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('正在連線到 Wi-Fi...')
        lcd.clear()
        lcd.putstr("Connecting to\nWi-Fi...")
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        start_time = time.ticks_ms()
        while not sta_if.isconnected():
            if time.ticks_diff(time.ticks_ms(), start_time) > 15000:
                print("Wi-Fi 連線失敗！")
                lcd.clear()
                lcd.putstr("Wi-Fi Connect\nFailed!")
                return False
            time.sleep_ms(100)
    print('網路已連線:', sta_if.ifconfig())
    return True

# --- NTP 時間同步函式 ---
def sync_time():
    print("正在同步 NTP 時間...")
    lcd.clear()
    lcd.putstr("Syncing Time...")
    try:
        ntptime.settime()
        print("NTP 時間同步成功")
        lcd.clear()
        lcd.putstr("Time Sync OK!")
        time.sleep_ms(500)
        return True
    except Exception as e:
        print(f"NTP 時間同步失敗: {e}")
        lcd.clear()
        lcd.putstr("Time Sync\nFailed!")
        time.sleep_ms(1000)
        return False

# --- 主程式 ---

# 初始化硬體
print("程式啟動，正在初始化硬體...")
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
devices = i2c.scan()
if not devices:
    raise RuntimeError("找不到 I2C LCD 設備")
lcd_addr = devices[0]
lcd = LCD1602.I2cLcd(i2c, lcd_addr, 2, 16)
dht_sensor = dht.DHT11(Pin(DHT_DATA_PIN))
rtc = RTC()

# 連線網路並同步時間
if connect_wifi():
    sync_time()

# 狀態變數
temperature = 0
humidity = 0

# 非阻塞式迴圈計時器
last_display_update_ticks = 0
last_sensor_read_ticks = -SENSOR_READ_INTERVAL_MS
last_ntp_sync_ticks = time.ticks_ms()

print("初始化完成，進入主迴圈...")

# --- 主迴圈 ---
while True:
    current_ticks = time.ticks_ms()

    # 任務1: 定期同步 NTP
    if time.ticks_diff(current_ticks, last_ntp_sync_ticks) >= NTP_SYNC_INTERVAL_MS:
        sync_time()
        last_ntp_sync_ticks = current_ticks

    # 任務2: 定期讀取溫濕度
    if time.ticks_diff(current_ticks, last_sensor_read_ticks) >= SENSOR_READ_INTERVAL_MS:
        try:
            dht_sensor.measure()
            temperature = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
            print(f"感測器讀取: Temp={temperature}C, Humi={humidity}%")
        except OSError as e:
            print(f"DHT 讀取錯誤: {e}")
        last_sensor_read_ticks = current_ticks

    # 任務3: 更新 LCD 顯示
    if time.ticks_diff(current_ticks, last_display_update_ticks) >= DISPLAY_UPDATE_INTERVAL_MS:
        # 取得加上時區偏移的時間
        current_time_utc = time.localtime()
        current_time_local = time.localtime(time.mktime(current_time_utc) + UTC_OFFSET * 3600)
        
        # 格式化時間字串
        time_str = f"{current_time_local[3]:02d}:{current_time_local[4]:02d}:{current_time_local[5]:02d}"
        
        # 將時間顯示在第一行
        lcd.move_to(0, 0)
        lcd.putstr(f"Time:   {time_str}")
        
        # 將溫濕度顯示在第二行
        temp_humi_str = f"T:{temperature:2d}{chr(223)}C  H:{humidity:2d}%"
        
        # === 這裡是修正的部分 ===
        # 舊的寫法 (錯誤的): lcd.putstr(temp_humi_str.ljust(16))
        # 新的寫法 (正確的): 使用 format() 方法來做左對齊並填充空格
        lcd.move_to(0, 1)
        lcd.putstr("{:<16}".format(temp_humi_str))

        last_display_update_ticks = current_ticks