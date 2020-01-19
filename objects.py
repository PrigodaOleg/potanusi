from collections.abc import Iterable

takes_synonyms = ['takes', 'take', 'consume', 'consumes']
gives_synonyms = ['gives', 'give', 'produce', 'produces']
constraints_synonyms = ['constraints', "dependency", "dependencies"]
reciprocal_synonyms = ['reciprocal']
name_synonyms = ['name']
type_synonyms = ['type']
module_synonyms = ['module']


def first_intersection(a, b):
    if isinstance(b, Iterable):
        for e in a:
            if e in b:
                return e
    return None


class Pin:
    @classmethod
    def parse(cls, name, parent_module, descriptor):
        parameters = {}
        reciprocal = {}
        if descriptor:
            for pin_attribute_name, pin_attribute_value in descriptor.items():
                # print('        ', pin_attribute_name, pin_attribute_value)
                if pin_attribute_name in name_synonyms:
                    name = pin_attribute_value
                elif pin_attribute_name in reciprocal_synonyms:
                    reciprocal = pin_attribute_value
                elif 'link' in pin_attribute_name:
                    pass
                else:
                    parameters[pin_attribute_name] = pin_attribute_value

        type_synonym = first_intersection(type_synonyms, parameters)
        if not type_synonym:
            type_synonym = type_synonyms[0]
            listed_name = name.split('_')
            if listed_name[-1].isdigit():
                parameters[type_synonym] = '_'.join(listed_name[:-1])
                if 'index' not in parameters:
                    parameters['index'] = int(listed_name[-1])
            else:
                parameters[type_synonym] = name
        if parameters[type_synonym] in parent_module.constraints:
            parameters.update(parent_module.constraints[parameters[type_synonym]])

        pin = cls(parent_module, parameters)
        pin.name = name
        pin.reciprocal = reciprocal
        return pin

    def __init__(self, module, parameters={}):
        self.name = None
        self.module = module
        self.connected_to = None
        self.parameters = parameters
        self.reciprocal = {}
        self.links = []

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
    @classmethod
    def parse(cls, parent, path, descriptor):
        items = descriptor.items()
        module = cls(parent, None, path)
        for attribute_name, attribute_value in items:
            type_synonym = first_intersection(type_synonyms, attribute_value)
            if attribute_name in name_synonyms:
                module.name = attribute_value
                # print(attribute_value)
            elif type_synonym and attribute_value[type_synonym] in module_synonyms:
                # Module in root
                module.children.append(cls.parse(module, path + ':' + attribute_name, attribute_value))
            elif attribute_name in takes_synonyms:
                for take_name, take_value in attribute_value.items():
                    # print('    ', take_name, take_value)
                    type_synonym = first_intersection(type_synonyms, take_value)
                    if type_synonym and take_value[type_synonym] in module_synonyms:
                        # Element is module, parse it recursively
                        module.children.append(cls.parse(module, path + ':' + take_name, take_value))
                    else:
                        # Element is pin, parse it
                        module.pins.append(Pin.parse(take_name, module, take_value))
            elif attribute_name in gives_synonyms:
                for give_name, give_value in attribute_value.items():
                    # print('    ', give_name, give_value)
                    type_synonym = first_intersection(type_synonyms, give_value)
                    if type_synonym and give_value[type_synonym] in module_synonyms:
                        # Element is module, parse it recursively
                        module.children.append(cls.parse(module, path + ':' + give_name, give_value))
                    else:
                        # Element is pin, parse it
                        module.pins.append(Pin.parse(give_name, module, give_value))

            elif attribute_name in constraints_synonyms:
                module.constraints.update(attribute_value)
            else:
                type_synonym = first_intersection(type_synonyms, attribute_value)
                if type_synonym in module_synonyms:
                    # Element is module, parse it recursively
                    module.children.append(cls.parse(module, path + ':' + attribute_name, attribute_value))
                else:
                    module.attributes[attribute_name] = attribute_value
        return module

    def __init__(self, parent, name, path):
        self.parent = parent
        self.name = name
        self.path = path
        self.pins = []
        self.attributes = {}
        self.children = []
        self.constraints = {}
        self.links = {}

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
