# main.py
import network
import time
import bluetooth
import ubinascii
import asyncio

# wifi setup
ssid = 'SomewhatPoweredByWiFi'
password = 'kayvaan1998'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

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

# def ble_irq_handler(event, data):
#     """Handle all BLE IRQ events"""
#     try:
#         if event == _IRQ_SCAN_RESULT:
#             handle_scan_result(data)
#         elif event == _IRQ_SCAN_DONE:
#             handle_scan_done()
#         elif event == _IRQ_PERIPHERAL_CONNECT:
#             handle_peripheral_connect(data)
#         elif event == _IRQ_PERIPHERAL_DISCONNECT:
#             handle_peripheral_disconnect(data)
#         elif event == _IRQ_GATTC_NOTIFY:
#             handle_notify(data)
#     except Exception as e:
#         print(f"\nError in BLE IRQ handler: {e}")

# def handle_scan_result(data):
#     """Handle scan result events"""
#     addr_type, addr, adv_type, rssi, adv_data = data
#     mac = ubinascii.hexlify(addr).decode('utf-8')
#     mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
    
#     decoded = decode_adv_data(adv_data)
#     name = decoded.get('name', '')
    
#     # Check if this is one of our target devices
#     if not PRIMARY_DEVICE['found'] or not PRIMARY_DEVICE['connected']:
#         # Match by MAC (exact) or name prefix (if name exists)
#         if mac.lower() == PRIMARY_DEVICE['mac'].lower() or (name and name.startswith(PRIMARY_DEVICE['name'])):
#             print(f"\nFound primary device: {PRIMARY_DEVICE['name']}")
#             print(f"MAC: {mac}")
#             print(f"RSSI: {rssi}dBm")
            
#             # Mark as found
#             PRIMARY_DEVICE['found'] = True
#             # Try to connect
#             try:
#                 print(f"Attempting to connect to primary device {mac}...")
#                 ble.gap_connect(addr_type, addr)
#                 print(f"Connection initiated for primary device {mac}.")
#                 print(f"Attempting to write command to primary device {mac}...")
                
#                 # attach notification for primary device
#                 try:
#                     ble.gattc_write(PRIMARY_DEVICE['conn_handle'], 
#                                     PRIMARY_DEVICE['cmd'][0], 
#                                     b'\x01')  # Example command, adjust as needed
#                 except Exception as e:
#                     print(f"Failed to write command to primary device {mac}: {e}")

#             except Exception as e:
#                 print(f"Failed to connect to primary device {mac}: {e}")

#     elif PRIMARY_DEVICE['connected'] and (not SECONDARY_DEVICE['found'] or not SECONDARY_DEVICE['connected']):
#         # Only try to connect to secondary if primary is connected
#         if mac.lower() == SECONDARY_DEVICE['mac'].lower() or (name and name.startswith(SECONDARY_DEVICE['name'])):
#             print(f"\nFound secondary device: {SECONDARY_DEVICE['name']}")
#             print(f"MAC: {mac}")
#             print(f"RSSI: {rssi}dBm")
            
#             # Mark as found
#             SECONDARY_DEVICE['found'] = True
#             # Try to connect
#             try:
#                 print(f"Attempting to connect to secondary device {mac}...")
#                 ble.gap_connect(addr_type, addr)
#             except Exception as e:
#                 print(f"Failed to connect to secondary device {mac}: {e}")
    
#     elif PRIMARY_DEVICE['connected'] and SECONDARY_DEVICE['connected']:
#         print("\nBoth target devices found and connected. Stopping scan.")
#         ble.gap_scan(None)  # Stop scanning

# def handle_scan_done():
#     """Handle scan completion"""
#     print("\nScan complete. Waiting before next scan...")

# def handle_peripheral_connect(data):
#     """Handle peripheral connection events"""
#     conn_handle, addr_type, addr = data
#     mac = ubinascii.hexlify(addr).decode('utf-8')
#     mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
    
#     # Determine which device connected
#     if mac.lower() == PRIMARY_DEVICE['mac'].lower():
#         PRIMARY_DEVICE['connected'] = True
#         PRIMARY_DEVICE['conn_handle'] = conn_handle
#         print(f"\nPrimary device connected successfully!")
#         print(f"Connection handle: {conn_handle}")
#     elif mac.lower() == SECONDARY_DEVICE['mac'].lower():
#         SECONDARY_DEVICE['connected'] = True
#         SECONDARY_DEVICE['conn_handle'] = conn_handle
#         print(f"\nSecondary device connected successfully!")
#         print(f"Connection handle: {conn_handle}")
#     else:
#         print(f"\nUnknown device connected: {mac}")

# def handle_peripheral_disconnect(data):
#     """Handle peripheral disconnection events"""
#     conn_handle, addr_type, addr = data
#     mac = ubinascii.hexlify(addr).decode('utf-8')
#     mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
    
#     # Determine which device disconnected
#     if mac.lower() == PRIMARY_DEVICE['mac'].lower():
#         print(f"\nPrimary device disconnected!")
#         PRIMARY_DEVICE['connected'] = False
#         PRIMARY_DEVICE['conn_handle'] = None
        
#         # Disconnect secondary device if it's connected
#         if SECONDARY_DEVICE['connected'] and SECONDARY_DEVICE['conn_handle'] is not None:
#             print("Disconnecting secondary device due to primary disconnect...")
#             try:
#                 ble.gap_disconnect(SECONDARY_DEVICE['conn_handle'])
#                 print("Secondary device disconnected successfully.")
#             except Exception as e:
#                 print(f"Error disconnecting secondary device: {e}")
#                 # Reset secondary device state anyway
#                 SECONDARY_DEVICE['connected'] = False
#                 SECONDARY_DEVICE['conn_handle'] = None
        
#         # Reset found status to allow reconnection
#         PRIMARY_DEVICE['found'] = False
#         SECONDARY_DEVICE['found'] = False
        
#     elif mac.lower() == SECONDARY_DEVICE['mac'].lower():
#         print(f"\nSecondary device disconnected!")
#         SECONDARY_DEVICE['connected'] = False
#         SECONDARY_DEVICE['conn_handle'] = None
#         # Reset found status to allow reconnection
#         SECONDARY_DEVICE['found'] = False
#     else:
#         print(f"\nUnknown device disconnected: {mac}")

# def handle_notify(data):
#     """Handle notification data from devices"""
#     conn_handle, value_handle, notify_data = data
    
#     try:
#         if conn_handle == PRIMARY_DEVICE['conn_handle']:
#             # Parse weight data
#             weight, battery = parse_weight_data(notify_data)
#             if weight is not None:
#                 PRIMARY_DEVICE['weight'] = weight
#                 PRIMARY_DEVICE['battery_level'] = battery
#                 # latest_readings['weight'] = weight
#                 # latest_readings['weight_battery'] = battery
#                 # latest_readings['timestamp'] = time.time()
#                 print(f"Weight: {weight:.2f} kg, Battery: {battery}%")
                
#         elif conn_handle == SECONDARY_DEVICE['conn_handle']:
#             # Parse pressure data
#             pressure, battery = parse_pressure_data(notify_data)
#             if pressure is not None:
#                 SECONDARY_DEVICE['pressure'] = pressure
#                 SECONDARY_DEVICE['battery_level'] = battery
#                 # latest_readings['pressure'] = pressure
#                 # latest_readings['pressure_battery'] = battery
#                 # latest_readings['timestamp'] = time.time()
#                 print(f"Pressure: {pressure:.2f} units, Battery: {battery}%")
                
#     except Exception as e:
#         print(f"Error parsing notification data: {e}")

# def scan_callback(event, data):
#     """Legacy scan callback for debugging (kept for compatibility)"""
#     try:
#         if event == _IRQ_SCAN_RESULT:
#             addr_type, addr, adv_type, rssi, adv_data = data
#             decoded = decode_adv_data(adv_data)
            
#             # Format MAC address
#             mac = ubinascii.hexlify(addr).decode('utf-8')
#             mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
            
#             print("\nFound device:")
#             print(f"  MAC: {mac}")
#             print(f"  Type: {addr_type}, Adv Type: {adv_type}, RSSI: {rssi}dBm")
#             if decoded['name']:
#                 print(f"  Name: {decoded['name']}")
#             if decoded['services']:
#                 print(f"  Services: {decoded['services']}")
#             if decoded['manufacturer']:
#                 print(f"  Manufacturer Data: {decoded['manufacturer']}")
#             if decoded['tx_power'] is not None:
#                 print(f"  TX Power: {decoded['tx_power']}dBm")
#             print(f"  Raw Data: {decoded['raw']}")
            
#         elif event == _IRQ_SCAN_DONE:
#             print("\nScan complete. Waiting before next scan...")
#     except Exception as e:
#         print(f"\nError in callback: {e}")

# def parse_weight_data(data):
#     """Parse weight data from BookooScale (20-byte format)"""
#     if len(data) == 20:
#         # Extract battery level from byte 13
#         battery_level = data[13]
        
#         # Extract weight from bytes 7, 8, 9 (24-bit integer)
#         weight = (
#             (data[7] << 16) +
#             (data[8] << 8) +
#             data[9]
#         )
        
#         # Check sign byte (byte 6)
#         if data[6] == 45:  # 45 is ASCII for '-'
#             weight = weight * -1
        
#         # Convert to final units (divide by 100)
#         weight_kg = weight / 100
        
#         return weight_kg, battery_level
#     return None, None

# def parse_pressure_data(data):
#     """Parse pressure data from BookooPressure sensor (10-byte format)"""
#     if len(data) == 10:
#         # Extract pressure from bytes 4 and 5 (16-bit value)
#         pressure_raw = (data[4] << 8) + data[5]
        
#         # Convert to final units (divide by 100)
#         pressure = pressure_raw / 100
        
#         # Note: Battery level information is not available in the pressure data
#         # from the TypeScript implementation - only pressure readings
#         battery_level = None
        
#         return pressure, battery_level
#     return None, None

# # main forever loop
# while True:
#     while not wlan.isconnected():
#         print("Attempting WiFi connection...")
#         time.sleep(1)

#     if wlan.isconnected():
#         print("\nWiFi Connected!")
#         print("Network config:", wlan.ifconfig())

#         # Scan for bluetooth devices
#         print("\nScanning for Bluetooth devices...")
#         print(f"Primary device connected: {PRIMARY_DEVICE['connected']}")
#         print(f"Secondary device connected: {SECONDARY_DEVICE['connected']}")
        
#         # Set up the IRQ handler for all BLE events
#         ble.irq(ble_irq_handler)

#         # Start scanning
#         ble.gap_scan(5000, 30000, 30000)  # Scan for 5 seconds, duty cycle of 0.03
        
#         # Start the asyncio event loop to handle data fetching
#         # asyncio.run(get_data())

#         # Wait for scan to complete before starting a new one
#         time.sleep(7)  # Wait longer than the scan duration