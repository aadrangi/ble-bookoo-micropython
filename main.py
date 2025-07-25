# main.py - Direct connection debug version
import network
import time
import ubluetooth
import ubinascii
import struct
import gc
from EventHandler import EventHandler

# garbage collection
gc.collect()
print("Free memory:", gc.mem_free())



# global wifi info
ssid = 'SomewhatPoweredByWiFi'
password = 'kayvaan1998'
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# global bluetooth setup
ble = ubluetooth.BLE()

# global BLE IRQ events
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

# global Target devices to find and connect
PRIMARY_DEVICE = {
    "name": "BOOKOO_SC",
    "mac": "d9:5d:10:01:41:7f",
    "services": {0X0FFE:None},
    "characteristics":{0xFF11:{"value_handle": None, "subscribed": False}},
    "cmd": {0xFF12:{"value_handle": None, "sent": False}},
    "found": False,
    "connected": False,
    "conn_handle": None,
    "connection_attempts": 0,
    "last_attempt": 0
}

# pressure pressure is ff02, pressure power is ff03
SECONDARY_DEVICE = {
    "name": "BOOKOO_EM",
    "mac": "c0:1d:b2:30:a1:78",
    "services": {0X0FFF,None},
    "characteristics":{0xFF02:{"value_handle": None, "subscribed": False}, 0xFF03:{"value_handle": None, "subscribed": False}},
    "cmd": {0xFF01:{"value_handle": None, "sent": False}},
    "found": False,
    "connected": False,
    "conn_handle": None,
    "extraction_inprogress": False,
    "connection_attempts": 0,
    "last_attempt": 0
}

def connect_wifi():
    """Handle WiFi connection"""
    if not wlan.isconnected():
        print("Attempting WiFi connection...")
        try:
            wlan.connect(ssid, password)
            timeout = 10
            while not wlan.isconnected() and timeout > 0:
                time.sleep(1)
                timeout -= 1
            if wlan.isconnected():
                print("WiFi connected successfully!")
                print("Network config:", wlan.ifconfig())
                return {"status": "connected"}
            else:
                print("WiFi connection timeout")
                return {"status": "timeout"}
        except Exception as e:
            print(f"Failed to connect to WiFi: {e}")
            return {"error": str(e)}
    else:
        return {"status": "already_connected"}

def connect_ble():
    """Connect to BLE devices directly"""
    current_time = time.time()
    
    # Try to connect to primary device
    if not PRIMARY_DEVICE['connected']:
        # Rate limit connection attempts (wait at least 3 seconds between attempts)
        if current_time - PRIMARY_DEVICE['last_attempt'] < 3:
            return {"status": "waiting_retry_primary"}
        
        try:
            print(f"Connection attempt #{PRIMARY_DEVICE['connection_attempts'] + 1} to PRIMARY device {PRIMARY_DEVICE['mac']}...")
            
            # Convert MAC address to bytes (ensure correct format)
            mac_str = PRIMARY_DEVICE['mac'].replace(':', '')
            print(f"MAC string without colons: {mac_str}")
            
            addr_bytes = ubinascii.unhexlify(mac_str)
            print(f"Address bytes: {ubinascii.hexlify(addr_bytes)}")
            print(f"Address bytes length: {len(addr_bytes)}")
            
            # Attempt connection
            ble.gap_connect(0x01, addr_bytes)
            
            PRIMARY_DEVICE['connection_attempts'] += 1
            PRIMARY_DEVICE['last_attempt'] = current_time
            
            print(f"Connection command sent for PRIMARY device")
            time.sleep(0.2)  # Small delay to allow connection command to process
            return {"status": "connecting_primary"}
            
        except Exception as e:
            print(f"Failed to connect to PRIMARY device: {e}")
            PRIMARY_DEVICE['connection_attempts'] += 1
            PRIMARY_DEVICE['last_attempt'] = current_time
            return {"error": f"primary_connect_failed: {e}"} 
    # Try to connect to secondary device if primary is connected
    elif PRIMARY_DEVICE['connected'] and not SECONDARY_DEVICE['connected']:
        if current_time - SECONDARY_DEVICE['last_attempt'] < 3:
            return {"status": "waiting_retry_secondary"}
        
        try:
            print(f"Connection attempt #{SECONDARY_DEVICE['connection_attempts'] + 1} to SECONDARY device {SECONDARY_DEVICE['mac']}...")
            
            mac_str = SECONDARY_DEVICE['mac'].replace(':', '')
            addr_bytes = ubinascii.unhexlify(mac_str)
            
            ble.gap_connect(0x01, addr_bytes)
            
            SECONDARY_DEVICE['connection_attempts'] += 1
            SECONDARY_DEVICE['last_attempt'] = current_time
            
            print(f"Connection command sent for SECONDARY device")
            time.sleep(0.2)  # Small delay to allow connection command to process
            return {"status": "connecting_secondary"}
            
        except Exception as e:
            print(f"Failed to connect to SECONDARY device: {e}")
            SECONDARY_DEVICE['connection_attempts'] += 1
            SECONDARY_DEVICE['last_attempt'] = current_time
            return {"error": f"secondary_connect_failed: {e}"}
    
    # Both devices connected
    elif PRIMARY_DEVICE['connected'] and SECONDARY_DEVICE['connected']:
        return {"status": "all_connected"}
    
    return {"status": "unknown_state"}

# def discover_services():
#     """Discover services for connected devices"""
#     if PRIMARY_DEVICE['connected'] and PRIMARY_DEVICE['conn_handle'] is not None:
#         try:
#             print(f"Discovering services for PRIMARY device {PRIMARY_DEVICE['mac']}...")
#             ble.gattc_discover_services(int(PRIMARY_DEVICE['conn_handle']))
#             time.sleep(0.2)  # Small delay to allow discovery command to process
#             return {"status": "discovering_primary"}
#         except Exception as e:
#             print(f"Failed to discover services for PRIMARY device: {e}")
#             return {"error": f"primary_service_discovery_failed: {e}"}
    
#     if SECONDARY_DEVICE['connected'] and SECONDARY_DEVICE['conn_handle'] is not None:
#         try:
#             print(f"Discovering services for SECONDARY device {SECONDARY_DEVICE['mac']}...")
#             ble.gattc_discover_services(int(SECONDARY_DEVICE['conn_handle']))
#             time.sleep(0.2)  # Small delay to allow discovery command to process
#             return {"status": "discovering_secondary"}
#         except Exception as e:
#             print(f"Failed to discover services for SECONDARY device: {e}")
#             return {"error": f"secondary_service_discovery_failed: {e}"}
    
#     return {"status": "no_device_connected"}

def discover_characteristics():
    """Discover characteristics for connected devices"""
    if PRIMARY_DEVICE['connected'] and PRIMARY_DEVICE['conn_handle'] is not None and PRIMARY_DEVICE['characteristics'][0xFF11]['value_handle'] is None:
        try:
            print(f"Discovering characteristics for PRIMARY device {PRIMARY_DEVICE['mac']}...")
            ble.gattc_discover_characteristics(int(PRIMARY_DEVICE['conn_handle']), 0x001, 0xffff)  # Discover all characteristics
            time.sleep(0.2)  # Small delay to allow discovery command to process
            return {"status": "discovering_primary"}
        except Exception as e:
            print(f"Failed to discover characteristics for PRIMARY device: {e}")
            return {"error": f"primary_discovery_failed: {e}"}
    
    if SECONDARY_DEVICE['connected'] and SECONDARY_DEVICE['conn_handle'] is not None and SECONDARY_DEVICE['characteristics'][0xFF02]['value_handle'] is None:
        try:
            print(f"Discovering characteristics for SECONDARY device {SECONDARY_DEVICE['mac']}...")
            ble.gattc_discover_characteristics(int(SECONDARY_DEVICE['conn_handle']), 0x001, 0xffff)  # Discover all characteristics
            time.sleep(0.2)  # Small delay to allow discovery command to process
            return {"status": "discovering_secondary"}
        except Exception as e:
            print(f"Failed to discover characteristics for SECONDARY device: {e}")
            return {"error": f"secondary_discovery_failed: {e}"}
    
    return {"status": "no_device_connected"}

# def read_ble_data():
#     """Read data from a BLE characteristic"""

#     # Primary device
#     try:
#         print(f"Reading data from characteristic {list(PRIMARY_DEVICE['characteristics'].keys())[0]} on connection handle {PRIMARY_DEVICE['conn_handle']}...")
#         ble.gattc_read(int(PRIMARY_DEVICE['conn_handle']), PRIMARY_DEVICE['characteristics'][0xFF11])
#         time.sleep(0.2)  # Small delay to allow read command to process
#     except Exception as e:
#         print(f"Failed to read from characteristic {list(PRIMARY_DEVICE['characteristics'].keys())[0]}: {e}")

#     # Secondary device
#     try:
#         print(f"Reading data from characteristic {list(SECONDARY_DEVICE['characteristics'].keys())[0]} on connection handle {SECONDARY_DEVICE['conn_handle']}...")
#         ble.gattc_read(int(SECONDARY_DEVICE['conn_handle']), SECONDARY_DEVICE['characteristics'][0xFF02])
#         time.sleep(0.2)  # Small delay to allow read command to process
#     except Exception as e:
#         print(f"Failed to read from characteristic {list(SECONDARY_DEVICE['characteristics'].keys())[0]}: {e}")

# def write_indication_request():
#     """Write an indication request to a BLE characteristic"""
#     # Primary device
#     try:
#         print(f"Writing indication request to characteristic {list(PRIMARY_DEVICE['characteristics'].keys())[0]} on connection handle {PRIMARY_DEVICE['conn_handle']}...")
#         ble.gattc_write(int(PRIMARY_DEVICE['conn_handle']), PRIMARY_DEVICE['characteristics'][0xFF11]+1,  b'\x02\x00')  # 0x02 for indication
#         time.sleep(0.2)  # Small delay to allow write command to process
#     except Exception as e:
#         print(f"Failed to write indication request for characteristic {list(PRIMARY_DEVICE['characteristics'].keys())[0]}: {e}")

#     # Secondary device
#     try:
#         print(f"Writing indication request to characteristic {list(SECONDARY_DEVICE['characteristics'].keys())[0]} on connection handle {SECONDARY_DEVICE['conn_handle']}...")
#         ble.gattc_write(int(SECONDARY_DEVICE['conn_handle']), SECONDARY_DEVICE['characteristics'][0xFF02]+1, b'\x02\x00')  # 0x02 for indication
#         time.sleep(0.2)  # Small delay to allow write command to process
#     except Exception as e:
#         print(f"Failed to write indication request for characteristic {list(SECONDARY_DEVICE['characteristics'].keys())[0]}: {e}")

def enable_notifications():
    """Enable notifications for BLE characteristics"""
    # Primary device
    if not PRIMARY_DEVICE['characteristics'][0xFF11]['subscribed']:
        try:
            print(f"Enabling notifications for characteristic {list(PRIMARY_DEVICE['characteristics'].keys())[0]} on connection handle {PRIMARY_DEVICE['conn_handle']}...")
            cccd_handle = PRIMARY_DEVICE['characteristics'][0xFF11]['value_handle'] + 1  # Assuming CCCD 
            ble.gattc_write(int(PRIMARY_DEVICE['conn_handle']), cccd_handle, b'\x01\x00', 1)  # 0x01 for notification
            time.sleep(0.2)  # Small delay to allow notification command to process
        except Exception as e:
            print(f"Failed to enable notifications for characteristic {list(PRIMARY_DEVICE['characteristics'].keys())[0]}: {e}")

    # Secondary device
    if not SECONDARY_DEVICE['characteristics'][0xFF02]['subscribed']:
        try:
            print(f"Enabling notifications for characteristic {list(SECONDARY_DEVICE['characteristics'].keys())[0]} on connection handle {SECONDARY_DEVICE['conn_handle']}...")
            cccd_handle = SECONDARY_DEVICE['characteristics'][0xFF02]['value_handle'] + 1 # Assuming CCCD
            ble.gattc_write(int(SECONDARY_DEVICE['conn_handle']), cccd_handle, b'\x01\x00', 1)


            SECONDARY_DEVICE['characteristics'][0xFF02]['subscribed'] = True  # Mark as subscribed
            print(f"Notifications enabled for secondary device characteristic {list(SECONDARY_DEVICE['characteristics'].keys())[0]}")
            if not SECONDARY_DEVICE['extraction_inprogress']:
                start_extraction()
                SECONDARY_DEVICE['cmd'][0xFF01]['sent'] = True
                print("Extraction started for secondary device.")
            else:
                print("Extraction already in progress for secondary device, skipping start command.")
              # Mark command as sent
            time.sleep(0.2)
        except Exception as e:
            print(f"Failed to enable notifications for characteristic {list(SECONDARY_DEVICE['characteristics'].keys())[0]}: {e}")

def start_extraction():
    """Start extraction process for secondary device"""
    try:
        print(f"Starting extraction for SECONDARY device {SECONDARY_DEVICE['mac']}...")
        start_extraction_command = b'\x02\x0C\x01\x00\x00\x00\x0f'  # Example command to start extraction
        ble.gattc_write(int(SECONDARY_DEVICE['conn_handle']), SECONDARY_DEVICE['cmd'][0xFF01]['value_handle'], start_extraction_command, 1)
        SECONDARY_DEVICE['extraction_inprogress'] = True
        print(f"Extraction started for secondary device {SECONDARY_DEVICE['mac']}")
    except Exception as e:
        print(f"Failed to start extraction for SECONDARY device: {e}")

def stop_extraction():
    """Stop extraction process for secondary device"""
    try:
        print(f"Stopping extraction for SECONDARY device {SECONDARY_DEVICE['mac']}...")
        stop_extraction_command = b'\x02\x0C\x00\x00\x00\x00\x0e'  # Example command to stop extraction
        ble.gattc_write(int(SECONDARY_DEVICE['conn_handle']), SECONDARY_DEVICE['cmd'][0xFF01]['value_handle'], stop_extraction_command, 1)
        SECONDARY_DEVICE['extraction_inprogress'] = False
        print(f"Extraction stopped for secondary device {SECONDARY_DEVICE['mac']}")
    except Exception as e:
        print(f"Failed to stop extraction for SECONDARY device: {e}")

# def notify_ble_data():
#     """Indicate data to a BLE characteristic"""

#     # Primary device
#     try:
#         print(f"Enabling notification for characteristic {list(PRIMARY_DEVICE['characteristics'].keys())[0]} on connection handle {PRIMARY_DEVICE['conn_handle']}...")
#         ble.gatts_notify(int(PRIMARY_DEVICE['conn_handle']), PRIMARY_DEVICE['characteristics'][0xFF11])
#         time.sleep(0.2)  # Small delay to allow read command to process
#     except Exception as e:
#         print(f"Failed to enable notification for characteristic {list(PRIMARY_DEVICE['characteristics'].keys())[0]}: {e}")

#     # Secondary device
#     try:
#         print(f"Enabling notification for characteristic {list(SECONDARY_DEVICE['characteristics'].keys())[0]} on connection handle {SECONDARY_DEVICE['conn_handle']}...")
#         ble.gatts_notify(int(SECONDARY_DEVICE['conn_handle']), SECONDARY_DEVICE['characteristics'][0xFF02])
#         time.sleep(0.2)  # Small delay to allow read command to process
#     except Exception as e:
#         print(f"Failed to enable notification for characteristic {list(SECONDARY_DEVICE['characteristics'].keys())[0]}: {e}")

def parse_weight_data(data):
    """
    Parse weight data from BookooScale (20-byte format)
    Input is a list of bytes (length 4)
    Where the first byte is the sign byte,
    bytes 8, 9, 10 are the weight bytes,
    """
    # if len(data) == 20:
    try:
        # weight = struct.unpack('>H', data[1:])/100
        # weight = int.from_bytes("\\".join(data[1:]), 'big')/100
        weight = (int(data[1],16) << 16) +\
                    (int(data[2],16) << 8) + \
                    int(data[3],16)
        if data[0] == 0x2d:
            sign = -1
        else:
            sign = 1
        weight*=sign/100  # Convert to grams
        print(f"Parsed weight: {weight} g")
        return weight
    except Exception as e:
        print(f"failed to parse weight data: {e}")
    return None, None

def parse_pressure_data(data):
    """Parse pressure data from BookooPressure sensor (10-byte format)"""
    # if len(data) == 10:
    try:
        # Extract pressure from bytes 4 and 5 (16-bit value)
        pressure_raw = (int(data[0],16) << 8) + int(data[1],16)
        
        # Convert to final units (divide by 100)
        pressure = pressure_raw / 100
        
        # Note: Battery level information is not available in the pressure data
        # from the TypeScript implementation - only pressure readings
        
        return pressure
    except Exception as e:
        print(f"failed to parse pressure data: {e}")
        return None
    return None, None


def handle_ble_connect(data):
    """Handle BLE connection events"""
    conn_handle, _, addr = data
    mac = ubinascii.hexlify(addr).decode('utf-8')
    mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
    
    print(f"\n=== BLE CONNECTION EVENT ===")
    print(f"Connected to: {mac}")
    print(f"Connection handle: {conn_handle}")
    
    # Determine which device connected
    if mac.lower() == PRIMARY_DEVICE['mac'].lower():
        print(f"*** PRIMARY DEVICE CONNECTED! ***")
        PRIMARY_DEVICE['connected'] = True
        PRIMARY_DEVICE['conn_handle'] = conn_handle
        print(f"Primary device handle: {PRIMARY_DEVICE['conn_handle']}")
    elif mac.lower() == SECONDARY_DEVICE['mac'].lower():
        print(f"*** SECONDARY DEVICE CONNECTED! ***")
        SECONDARY_DEVICE['connected'] = True
        SECONDARY_DEVICE['conn_handle'] = conn_handle
        print(f"Secondary device handle: {SECONDARY_DEVICE['conn_handle']}")
    else:
        print(f"*** UNKNOWN DEVICE CONNECTED: {mac} ***")
    
    time.sleep(0.2)  # Small delay to allow connection to stabilize
    print(f"============================")

def handle_ble_disconnect(data):
    """Handle BLE disconnection events"""
    _, _, addr = data
    mac = ubinascii.hexlify(addr).decode('utf-8')
    mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
    
    print(f"\n=== BLE DISCONNECTION EVENT ===")
    print(f"Disconnected from: {mac}")
    
    # Determine which device disconnected
    if mac.lower() == PRIMARY_DEVICE['mac'].lower():
        print(f"*** PRIMARY DEVICE DISCONNECTED! ***")
        PRIMARY_DEVICE['connected'] = False
        PRIMARY_DEVICE['conn_handle'] = None
        
        # Disconnect secondary device if it's connected
        if SECONDARY_DEVICE['connected'] and SECONDARY_DEVICE['conn_handle'] is not None:
            print("Disconnecting secondary device due to primary disconnect...")
            try:
                ble.gap_disconnect(SECONDARY_DEVICE['conn_handle'])
                # stop_extraction_command = b'\x02\x0C\x00\x00\x00\x00\x0e'
                # ble.gattc_write(int(SECONDARY_DEVICE['conn_handle']), SECONDARY_DEVICE['characteristics'][0xFF02] + 1, stop_extraction_command, 1)  # Disable notifications
                SECONDARY_DEVICE['connected'] = False
                SECONDARY_DEVICE['conn_handle'] = None
                if SECONDARY_DEVICE['extraction_inprogress']:
                    print("Stopping extraction for secondary device...")
                    stop_extraction()
                    SECONDARY_DEVICE['cmd'][0xFF01]['sent'] = False
                else:
                    print("No extraction in progress for secondary device.")
            except Exception as e:
                print(f"Error disconnecting secondary device: {e}")
        
    elif mac.lower() == SECONDARY_DEVICE['mac'].lower():
        print(f"*** SECONDARY DEVICE DISCONNECTED! ***")
        SECONDARY_DEVICE['connected'] = False
        SECONDARY_DEVICE['conn_handle'] = None
    else:
        print(f"*** UNKNOWN DEVICE DISCONNECTED: {mac} ***")
    
    print(f"==============================")

# def handle_ble_read_result(data):
#     """Handle BLE read result events"""
#     conn_handle, value_handle, value = data
#     print(f"\n=== BLE READ RESULT EVENT ===")
#     print(f"All data: {data}")
#     # print(f"length of bits returned: {len(value)}")
#     mac = None
    
#     # Determine which device the read result is for
#     if conn_handle == PRIMARY_DEVICE['conn_handle']:
#         mac = PRIMARY_DEVICE['mac']
#         print(f"\n=== READ RESULT FROM PRIMARY DEVICE ===")
#         try:            # Parse weight data from the value
#             result = parse_weight_data(value)
#             print(f"Parsed weight data: {result}")
#         except Exception as e:
#             print(f"Error parsing weight data: {e}")
#             result = None
#     elif conn_handle == SECONDARY_DEVICE['conn_handle']:
#         mac = SECONDARY_DEVICE['mac']
#         print(f"\n=== READ RESULT FROM SECONDARY DEVICE ===")
#         try:
#             # Parse pressure data from the value
#             result = parse_pressure_data(value)
#             print(f"Parsed pressure data: {result}")
#         except Exception as e:
#             print(f"Error parsing pressure data: {e}")
#             result = None
#     else:
#         print(f"\n=== READ RESULT FROM UNKNOWN DEVICE ===")
    
    # if mac:
    #     print(f"Device MAC: {mac}")
    #     print(f"Connection handle: {conn_handle}")
    #     print(f"Value handle: {value_handle}")
    #     print(f"Value: {value}")
    #     print(f"Value: {ubinascii.hexlify(value).decode('utf-8')}")
    # else:
    #     print("No matching device found for read result.")
    
    # print(f"=======================================")

# def handle_ble_discovered_services(data):
#     """Handle discovered services events"""
#     # conn_handle, start_handle, end_handle, uuid = data
#     print(f"\n=== BLE DISCOVERED SERVICES EVENT ===")
    
#     # Convert UUID to string for display
#     # uuid_str = ubinascii.hexlify(uuid).decode('utf-8')
#     print(f"all data: {data}")
#     # Determine which device the service belongs to
#     # if conn_handle == PRIMARY_DEVICE['conn_handle']:
#     #     print(f"Discovered services for PRIMARY device {PRIMARY_DEVICE['mac']}:")
#     #     PRIMARY_DEVICE['found'] = True
#     #     print(f"All data: {data}")
#     #     # print(f"UUID: {uuid_str}, Start Handle: {start_handle}, End Handle: {end_handle}")
#     # elif conn_handle == SECONDARY_DEVICE['conn_handle']:
#     #     print(f"Discovered services for SECONDARY device {SECONDARY_DEVICE['mac']}:")
#     #     SECONDARY_DEVICE['found'] = True
#     #     # print(f"UUID: {uuid_str}, Start Handle: {start_handle}, End Handle: {end_handle}")
#     # else:
#     #     print(f"Discovered services for UNKNOWN device:")
#     #     # print(f"UUID: {uuid_str}, Start Handle: {start_handle}, End Handle: {end_handle}")

#     print(f"==============================")

def handle_ble_discovered_characteristics(data):
    """Handle discovered characteristics events"""
    conn_handle, _, value_handle, _, uuid = data
    print(f"\n=== BLE DISCOVERED CHARACTERISTICS EVENT ===")
    print(f"All data for discovered characteristics: {data}")
    # decode the uuid
    uuid = struct.unpack('<H', uuid)[0]  # Assuming UUID is a 16-bit value

    # Convert UUID to string for display
    # uuid_str = ubinascii.hexlify(uuid).decode('utf-8')
    # Determine which device the characteristics belong to
    if conn_handle == PRIMARY_DEVICE['conn_handle']:
        print(f"Discovered characteristics for PRIMARY device {PRIMARY_DEVICE['mac']}:")
        # print(f"Attempting to discover attributes of ble uuid class: {uuid.__dict__}")
        if uuid in list(PRIMARY_DEVICE['characteristics'].keys()):
            print(f"Located data for characteristic {uuid}")
            print(f"all data below for the characteristic: {data}")
            print(f"Assigning value handle {value_handle} to characteristic")
            PRIMARY_DEVICE['characteristics'][uuid]['value_handle'] = value_handle
        else:
            print(f"UUID {uuid} for {PRIMARY_DEVICE['name']} does not have a known characteristic")
    elif conn_handle == SECONDARY_DEVICE['conn_handle']:
        print(f"Discovered characteristics for SECONDARY device {SECONDARY_DEVICE['mac']}:")
        if uuid in list(SECONDARY_DEVICE['characteristics'].keys()):
            print(f"Located data for characteristic {uuid}")
            print(f"all data below for the characteristic: {data}")
            print(f"Assigning value handle {value_handle} to characteristic")
            SECONDARY_DEVICE['characteristics'][uuid]['value_handle'] = value_handle
        elif uuid in list(SECONDARY_DEVICE['cmd'].keys()):
            print(f"Located data for command {uuid}")
            print(f"all data below for the command: {data}")
            print(f"Assigning value handle {value_handle} to command")
            SECONDARY_DEVICE['cmd'][uuid]['value_handle'] = value_handle
        else:
            print(f"UUID {uuid} for {SECONDARY_DEVICE['name']} does not have a known characteristic")

    else:
        print(f"Discovered characteristics for UNKNOWN device:")
    
    print(f"============================================")

def handle_ble_notify(data):
    """Handle BLE notification events"""
    conn_handle, value_handle, value = data
    print(f"\n=== BLE NOTIFICATION EVENT ===")
    print(f"Connection handle: {conn_handle}, Value handle: {value_handle}, Value: {value.hex()}")
    paired_bytes = [value.hex()[i:i+2] for i in range(0, len(value.hex()), 2)]  # Convert to list of bytes
    print(f"Paired bytes: {paired_bytes}")

    # Determine which device the notification belongs to
    if conn_handle == PRIMARY_DEVICE['conn_handle']:
        print(f"Notification from PRIMARY device {PRIMARY_DEVICE['mac']}")
        print(f"Attempting to parse weight data from notification value: {value.hex()}")
        weight_bytes = paired_bytes[6:10]  # Extract bytes 7, 8, 9, 10 (0-indexed)
        try:
            weight = parse_weight_data(weight_bytes)
            print(f"Parsed weight: {weight} g")
        except Exception as e:
            print(f"Error parsing weight data: {e}")
            weight = None
        # Handle primary device notification logic here
    elif conn_handle == SECONDARY_DEVICE['conn_handle']:
        print(f"Notification from SECONDARY device {SECONDARY_DEVICE['mac']}")
        print(f"Attempting to parse pressure data from notification value: {value.hex()}")
        pressure_bytes = paired_bytes[4:6]  # Extract bytes 5, 6 (0-indexed)
        try:
            pressure = parse_pressure_data(pressure_bytes)
            print(f"Parsed pressure: {pressure} bars")
        except Exception as e:
            print(f"Error parsing pressure data: {e}")
            pressure = None
        # Handle secondary device notification logic here
    else:
        print("Notification from UNKNOWN device")

    print(f"=======================================")

# def handle_ble_indicate(data):
#     """Handle BLE indication events"""
#     conn_handle, value_handle, value = data
#     print(f"\n=== BLE INDICATION EVENT ===")
#     print(f"Connection handle: {conn_handle}, Value handle: {value_handle}, Value: {value}")

#     # Determine which device the indication belongs to
#     if conn_handle == PRIMARY_DEVICE['conn_handle']:
#         print(f"Indication from PRIMARY device {PRIMARY_DEVICE['mac']}")
#         # Handle primary device indication logic here
#     elif conn_handle == SECONDARY_DEVICE['conn_handle']:
#         print(f"Indication from SECONDARY device {SECONDARY_DEVICE['mac']}")
#         # Handle secondary device indication logic here
#     else:
#         print("Indication from UNKNOWN device")

#     print(f"=======================================")

def ble_irq_handler(event, data):
    print(f"\n=== BLE IRQ EVENT: {event} ===")
    """Handle all BLE IRQ events"""
    try:
        if event == _IRQ_PERIPHERAL_CONNECT:
            handle_ble_connect(data)
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            handle_ble_disconnect(data)
        # elif event == _IRQ_GATTC_READ_DONE:
        #     handle_ble_read_result(data)
        # elif event == _IRQ_GATTC_SERVICE_RESULT:
        #     handle_ble_discovered_services(data)
        # elif event == _IRQ_GATTC_INDICATE:
        #     handle_ble_indicate(data)
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            handle_ble_discovered_characteristics(data)
        elif event == _IRQ_GATTC_NOTIFY:
            handle_ble_notify(data)
            # handle_ble_indicate(data)
        else:
            # Print unknown events for debugging
            print(f"Unknown BLE IRQ event: {event}")
    except Exception as e:
        print(f"\nError in BLE IRQ handler: {e}")
        import sys
        sys.print_exception(e)

def debug_status():
    """Print current status for debugging"""
    print(f"\n=== STATUS DEBUG ===")
    print(f"WiFi connected: {wlan.isconnected()}")
    print(f"BLE active: {ble.active()}")
    print(f"PRIMARY - Connected: {PRIMARY_DEVICE['connected']}, Attempts: {PRIMARY_DEVICE['connection_attempts']}")
    print(f"SECONDARY - Connected: {SECONDARY_DEVICE['connected']}, Attempts: {SECONDARY_DEVICE['connection_attempts']}")
    
    if PRIMARY_DEVICE['connected']:
        print(f"PRIMARY handle: {PRIMARY_DEVICE['conn_handle']}")
    if SECONDARY_DEVICE['connected']:
        print(f"SECONDARY handle: {SECONDARY_DEVICE['conn_handle']}")
    
    print(f"PRIMARY characteristics: {PRIMARY_DEVICE['characteristics']}")
    print(f"SECONDARY characteristics: {SECONDARY_DEVICE['characteristics']}")

    print(f"==================")
    return {"status": "debug_printed"}

class MainApp:
    def __init__(self):
        print("Initializing MainApp...")
        self.event_handler = EventHandler()
        # Setup the IRQ handler once during initialization
        ble.irq(ble_irq_handler)
        print("BLE IRQ handler set up")
    
    def setup_functions(self):
        """Setup functions to be called periodically"""
        self.event_handler.register_function(connect_wifi, interval=15)
        self.event_handler.register_function(connect_ble, interval=2)  # Try every 2 seconds
        self.event_handler.register_function(debug_status, interval=10)  # Debug every 10 seconds
        # self.event_handler.register_function(discover_services, interval=0.5)
        # self.event_handler.register_function(write_indication_request, interval=0.5)
        self.event_handler.register_function(discover_characteristics, interval=0.5)
        self.event_handler.register_function(enable_notifications, interval=0.5)
        # self.event_handler.register_function(read_ble_data, interval=1.5)

    def run(self):
        """Main run loop - never blocks"""
        print("Starting event handler...")
        
        # Setup the periodic functions
        self.setup_functions()
        
        while True:
            try:
                # Run one cycle of the event handler
                self.event_handler.run_cycle()
                
                # Small sleep to prevent busy waiting
                time.sleep(1)  # 1s sleep
                
            except KeyboardInterrupt:
                print("Stopping...")
                break
            except Exception as e:
                print(f"Main loop error: {e}")
                import sys
                sys.print_exception(e)
                time.sleep(1)  # Wait before continuing

# Usage
if __name__ == "__main__":
    print("Starting MainApp...")
    print("BLE MAC addresses:")
    print(f"  Primary: {PRIMARY_DEVICE['mac']}")
    print(f"  Secondary: {SECONDARY_DEVICE['mac']}")
    
    # garbage collection and ble initialization
    gc.collect()
    print("Free memory after initialization:", gc.mem_free())
    ble.active(False)
    ble.active(True)
    print("BLE active:", ble.active())

    try:
        # Initialize and run the main application
        app = MainApp()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        # Print stack trace for debugging
        import sys
        sys.print_exception(e)