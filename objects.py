class Pin:
    def __init__(self, module, parameters):
        self.module = module
        self.connected_to = None
        self.parameters = parameters

    def connect(self, pin):
        for parameter in self.parameters:
            if parameter in pin.parameters:
                self.connected_to = pin
                pin.connected_to = self


class Module:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.pins = []

    def connect(self, module):
        pass
