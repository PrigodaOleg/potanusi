class Pin:
    def __init__(self, module, parameters={}):
        self.name = None
        self.module = module
        self.connected_to = None
        self.parameters = parameters
        self.reciprocal = {}

    def __str__(self):
        return 'Pin {}: parameters: {}'.format(self.name, self.parameters)

    def __repr__(self):
        return 'Pin {}: parameters: {}'.format(self.name, self.parameters)

    def connect(self, pin):
        for parameter in self.parameters:
            if parameter in pin.parameters:
                self.connected_to = pin
                pin.connected_to = self


class Module:
    def __init__(self, parent, name, path):
        self.parent = parent
        self.name = name
        self.path = path
        self.pins = []
        self.attributes = {}
        self.children = []
        self.constraints = {}

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        repr = '\nModule {}: name: {}, attributes: {}'.format(self.path, self.name, self.attributes)
        for pin in self.pins:
            repr += '\n    ' + str(pin)
        for child in self.children:
            repr += '\n    ' + str(child)
        return repr

    def connect(self, module):
        pass
