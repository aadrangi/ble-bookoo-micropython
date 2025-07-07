# main.py - Direct connection debug version
import network
import time
import bluetooth
import ubinascii
from EventHandler import EventHandler

# global wifi info
ssid = 'SomewhatPoweredByWiFi'
password = 'kayvaan1998'
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# global bluetooth setup
ble = bluetooth.BLE()
ble.active(True)

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
    "services": ['0FFE'],
    "characteristics":['FF11'],
    "cmd": ['FF12'],
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
    "services": ['0FFF'],
    "characteristics":['FF02', 'FF03'],
    "cmd": ['FF01'],
    "found": False,
    "connected": False,
    "conn_handle": None,
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
            ble.gap_connect(1, addr_bytes)
            
            PRIMARY_DEVICE['connection_attempts'] += 1
            PRIMARY_DEVICE['last_attempt'] = current_time
            
            print(f"Connection command sent for PRIMARY device")
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
            
            ble.gap_connect(2, addr_bytes)
            
            SECONDARY_DEVICE['connection_attempts'] += 1
            SECONDARY_DEVICE['last_attempt'] = current_time
            
            print(f"Connection command sent for SECONDARY device")
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

def handle_ble_connect(data):
    """Handle BLE connection events"""
    _, conn_handle, addr = data
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
                SECONDARY_DEVICE['connected'] = False
                SECONDARY_DEVICE['conn_handle'] = None
            except Exception as e:
                print(f"Error disconnecting secondary device: {e}")
        
    elif mac.lower() == SECONDARY_DEVICE['mac'].lower():
        print(f"*** SECONDARY DEVICE DISCONNECTED! ***")
        SECONDARY_DEVICE['connected'] = False
        SECONDARY_DEVICE['conn_handle'] = None
    else:
        print(f"*** UNKNOWN DEVICE DISCONNECTED: {mac} ***")
    
    print(f"==============================")

def ble_irq_handler(event, data):
    """Handle all BLE IRQ events"""
    try:
        if event == _IRQ_PERIPHERAL_CONNECT:
            handle_ble_connect(data)
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            handle_ble_disconnect(data)
        elif event == _IRQ_GATTC_NOTIFY:
            # TODO: handle notifications
            pass
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
                time.sleep(0.01)  # 10ms sleep
                
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
    
    try:
        # Initialize and run the main application
        app = MainApp()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        # Print stack trace for debugging
        import sys
        sys.print_exception(e)