import simplepyble

class Adapter:

    def __init__(self):
        self.adapter = simplepyble.Adapter.get_adapters()[0]

        self.peripherals = []

    def scan(self, duration=1):
        self.adapter.scan_for(duration)
        self.peripherals = self.adapter.scan_get_results()
    
    def set_callback_on_scan_start(self):
        self.adapter.set_callback_on_scan_start(lambda: print("Scan started."))
    
    def set_callback_on_scan_stop(self):
        self.adapter.set_callback_on_scan_stop(lambda: print("Scan complete."))

    def set_callback_on_scan_found(self):
        self.adapter.set_callback_on_scan_found(lambda peripheral: print(f"Found {peripheral.identifier()} [{peripheral.address()}]"))

    def get_peripheral(self, name):
        for p in self.peripherals:
            if p.identifier() == name:
                return p
        return None