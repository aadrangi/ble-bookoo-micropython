# main.py
import network
import time
import bluetooth
import ubinascii
import asyncio
from EventHandler import EventHandler

# wifi setup
ssid = 'SomewhatPoweredByWiFi'
password = 'kayvaan1998'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)


# bluetooth setup
ble = bluetooth.BLE()
ble.active(True)

# BLE IRQ events
_IRQ_CENTRAL_CONNECT = 1
_IRQ_CENTRAL_DISCONNECT = 2
_IRQ_GATTS_WRITE = 3
_IRQ_GATTS_READ_REQUEST = 4
_IRQ_SCAN_RESULT = 5
_IRQ_SCAN_DONE = 6
_IRQ_PERIPHERAL_CONNECT = 7
_IRQ_PERIPHERAL_DISCONNECT = 8
_IRQ_GATTC_SERVICE_RESULT = 9
_IRQ_GATTC_SERVICE_DONE = 10
_IRQ_GATTC_CHARACTERISTIC_RESULT = 11
_IRQ_GATTC_CHARACTERISTIC_DONE = 12
_IRQ_GATTC_DESCRIPTOR_RESULT = 13
_IRQ_GATTC_DESCRIPTOR_DONE = 14
_IRQ_GATTC_READ_RESULT = 15
_IRQ_GATTC_READ_DONE = 16
_IRQ_GATTC_WRITE_DONE = 17
_IRQ_GATTC_NOTIFY = 18
_IRQ_GATTC_INDICATE = 19

# Target devices to find and connect
PRIMARY_DEVICE = {
    "name": "BOOKOO_SC",
    "mac": "d9:5d:10:01:41:7f",
    "services": ['0FFE'],
    "characteristics":['FF11'],
    "cmd": ['FF12'],
    "found": False,
    "connected": False,
    "conn_handle": None,
}

# pressure pressure is ff02, pressure power is ff03
SECONDARY_DEVICE = {
    "name": "BOOKOO_EM",
    "mac": "c0:1d:b2:30:a1:78",
    "services": ['0FFF'],
    "characteristics":['FF02', 'FF03'],
    "cmd": ['FF01'],
    "found": False,
    "connected": False,
    "conn_handle": None,
}


def decode_adv_data(adv_data):
    """Decode BLE advertising data from memoryview/bytes into readable format"""
    if isinstance(adv_data, memoryview):
        adv_data = bytes(adv_data)
    
    result = {
        'name': None,
        'services': [],
        'manufacturer': None,
        'tx_power': None,
        'raw': ubinascii.hexlify(adv_data).decode('utf-8')
    }
    
    i = 0
    while i + 1 < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        
        if i + 1 + length > len(adv_data):
            break
            
        adv_type = adv_data[i + 1]
        data = adv_data[i + 2:i + 1 + length]
        
        # Complete or shortened local name
        if adv_type in (0x08, 0x09):
            try:
                result['name'] = data.decode('utf-8').strip()
            except:
                pass
        # TX Power Level
        elif adv_type == 0x0A:
            result['tx_power'] = int(data[0]) if data else None
        # 16-bit Service UUIDs
        elif adv_type in (0x02, 0x03):
            for j in range(0, len(data), 2):
                uuid = ubinascii.hexlify(data[j:j+2]).decode('utf-8')
                result['services'].append(uuid)
        # Manufacturer Specific Data
        elif adv_type == 0xFF:
            result['manufacturer'] = ubinascii.hexlify(data).decode('utf-8')
            
        i += 1 + length
    
    return result

def connect_wifi():
    """Handle WiFi connection and scanning for BLE devices"""
    while not wlan.isconnected():
        print("Attempting WiFi connection...")
        try:
            wlan.connect(ssid, password)
            if wlan.isconnected():
                print("WiFi connected successfully!")
                print("Network config:", wlan.ifconfig())
        except Exception as e:
            print(f"Failed to connect to WiFi: {e}")

def connect_ble():
    """ Connect to the primary and secondary device BLE device """
    while not PRIMARY_DEVICE['connected'] or not SECONDARY_DEVICE['connected']:
        if not PRIMARY_DEVICE['connected']:
            try:
                print(f"Trying to connect to primary device {PRIMARY_DEVICE['mac']}...")
                ble.gap_connect(0, ubinascii.unhexlify(PRIMARY_DEVICE['mac'].replace(':', '')))
            except Exception as e:
                print(f"Failed to connect to primary device: {e}")
        
        if PRIMARY_DEVICE['connected'] and not SECONDARY_DEVICE['connected']:
            try:
                print(f"Trying to connect to secondary device {SECONDARY_DEVICE['mac']}...")
                ble.gap_connect(0, ubinascii.unhexlify(SECONDARY_DEVICE['mac'].replace(':', '')))
            except Exception as e:
                print(f"Failed to connect to secondary device: {e}")

def handle_ble_connect(data):
    """
    assign connection handle and update connection status
    """
    _, conn_handle, addr = data
    mac = ubinascii.hexlify(addr).decode('utf-8')
    mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
    
    # Determine which device connected
    if mac.lower() == PRIMARY_DEVICE['mac'].lower():
        print(f"\nPrimary device connected: {mac}")
        PRIMARY_DEVICE['connected'] = True
        PRIMARY_DEVICE['conn_handle'] = conn_handle
    elif mac.lower() == SECONDARY_DEVICE['mac'].lower():
        print(f"\nSecondary device connected: {mac}")
        SECONDARY_DEVICE['connected'] = True
        SECONDARY_DEVICE['conn_handle'] = conn_handle
    else:
        print(f"\nUnknown device connected: {mac}")

def handle_ble_disconnect(data):
    """
    Handle peripheral disconnection events.
    Not asynchronous, but called from the BLE IRQ handler.
    """
    _, _, addr = data
    mac = ubinascii.hexlify(addr).decode('utf-8')
    mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
    
    # Determine which device disconnected
    if mac.lower() == PRIMARY_DEVICE['mac'].lower():
        print(f"\nPrimary device disconnected!")
        PRIMARY_DEVICE['connected'] = False
        PRIMARY_DEVICE['conn_handle'] = None

        # Disconnect secondary device if it's connected
        if SECONDARY_DEVICE['connected'] and SECONDARY_DEVICE['conn_handle'] is not None:
            print("Disconnecting secondary device due to primary disconnect...")
            try:
                ble.gap_disconnect(SECONDARY_DEVICE['conn_handle'])
                print("Secondary device disconnected successfully.")
                SECONDARY_DEVICE['connected'] = False
                SECONDARY_DEVICE['conn_handle'] = None
            except Exception as e:
                print(f"Error disconnecting secondary device: {e}")
        
    elif mac.lower() == SECONDARY_DEVICE['mac'].lower():
        print(f"\nSecondary device disconnected!")
        SECONDARY_DEVICE['connected'] = False
        SECONDARY_DEVICE['conn_handle'] = None
    else:
        print(f"\nUnknown device disconnected: {mac}")

def ble_irq_handler(event, data):
    """Handle all BLE IRQ events"""
    try:
        if event == _IRQ_PERIPHERAL_CONNECT:
            handle_ble_connect(data)
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            handle_ble_disconnect(data)
        elif event == _IRQ_GATTC_NOTIFY:
            # TODO
            # handle_notify(data)
            return
    except Exception as e:
        print(f"\nError in BLE IRQ handler: {e}")

class MainApp:
    def __init__(self):
        self.event_handler = EventHandler()
    
    def setup_functions(self):
        """Setup functions to be called periodically"""
        self.event_handler.add_function(connect_wifi(), interval=10, name='WiFi Handler')
        self.event_handler.add_function(connect_ble(), interval=5, name='BLE Connect Handler')
    
    def run(self):
        """Main run loop - never blocks"""
        print("Starting event handler...")
        
        while True:
            try:

                # setup the IRQ handler
                ble.irq(ble_irq_handler)

                # Run one cycle of the event handler
                self.event_handler.run_cycle()
                
                # Small sleep to prevent busy waiting
                time.sleep(0.01)  # 10ms sleep
                
            except KeyboardInterrupt:
                print("Stopping...")
                break
            except Exception as e:
                print(f"Main loop error: {e}")
                time.sleep(1)  # Wait before continuing