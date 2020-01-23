from collections.abc import Iterable
from itertools import chain

takes_synonyms = ['takes', 'take', 'consume', 'consumes']
gives_synonyms = ['gives', 'give', 'produce', 'produces']
constraints_synonyms = ['constraints', "dependency", "dependencies"]
reciprocal_synonyms = ['reciprocal']
name_synonyms = ['name']
type_synonyms = ['type']
module_synonyms = ['module']
link_synonyms = ['link', 'links']
index_synonyms = ['index']


def first_intersection(a, b):
    if isinstance(b, Iterable):
        for e in a:
            if e in b:
                return e
    return None


def is_pins_connectable(p1, p2):
    for parameter in p1.parameters:
        if parameter in p2.parameters:
            print(parameter, p1.parameters[parameter], p2.parameters[parameter])
            return True
    return False


class Pin:
    @classmethod
    def parse(cls, name, parent_module, descriptor):
        parameters = {}
        reciprocal = {}
        links = []
        if descriptor:
            if type(descriptor) == str:
                links.append(descriptor)
            else:
                for pin_attribute_name, pin_attribute_value in descriptor.items():
                    if pin_attribute_name in name_synonyms:
                        name = pin_attribute_value
                    elif pin_attribute_name in reciprocal_synonyms:
                        reciprocal = pin_attribute_value
                    elif pin_attribute_name in link_synonyms:
                        links.append(pin_attribute_value)
                    else:
                        parameters[pin_attribute_name] = pin_attribute_value

        type_synonym = first_intersection(type_synonyms, parameters)
        if not type_synonym:
            type_synonym = type_synonyms[0]
            listed_name = name.split('_')
            if listed_name[-1].isdigit():
                parameters[type_synonym] = '_'.join(listed_name[:-1])
                index_synonym = first_intersection(index_synonyms, parameters)
                if not index_synonym:
                    index_synonym = index_synonyms[0]
                    parameters[index_synonym] = int(listed_name[-1])
            else:
                parameters[type_synonym] = name
        if parameters[type_synonym] in parent_module.constraints:
            parameters.update(parent_module.constraints[parameters[type_synonym]])

        pin = cls(parent_module, parameters)
        pin.name = name
        pin.reciprocal = reciprocal
        pin.links = links
        return pin

    def __init__(self, module, parameters={}):
        self.name = None
        self.module = module
        self.connected_to = []
        self.parameters = parameters
        self.reciprocal = {}
        self.links = []

    def __str__(self):
        repr = 'Pin {}: parameters: {}'.format(self.name, self.parameters)
        for connected_pin in self.connected_to:
            repr += '\n        Connected to: {}:{}'.format(connected_pin.module.name, connected_pin.name)
        return repr

    def __repr__(self):
        return self.__str__()

    def connect(self, pin):
        if is_pins_connectable(self, pin):
            self.connected_to.append(pin)
            pin.connected_to.append(self)


class Module:
    parse_recurse_deep_counter = 0
    @classmethod
    def parse(cls, parent, path, descriptor):
        cls.parse_recurse_deep_counter += 1

        links = {}
        items = descriptor.items()
        module = cls(parent, None, path)
        for attribute_name, attribute_value in items:
            type_synonym = first_intersection(type_synonyms, attribute_value)
            if attribute_name in name_synonyms:
                module.name = attribute_value
            elif type_synonym and attribute_value[type_synonym] in module_synonyms:
                # Module in root
                module.children.append(cls.parse(module, path + ':' + attribute_name, attribute_value))
            elif attribute_name in takes_synonyms:
                for take_name, take_value in attribute_value.items():
                    type_synonym = first_intersection(type_synonyms, take_value)
                    if type_synonym and take_value[type_synonym] in module_synonyms:
                        # Element is module, parse it recursively
                        module.children.append(cls.parse(module, path + ':' + take_name, take_value))
                    else:
                        # Element is pin, parse it
                        module.take_pins[take_name] = Pin.parse(take_name, module, take_value)
            elif attribute_name in gives_synonyms:
                for give_name, give_value in attribute_value.items():
                    type_synonym = first_intersection(type_synonyms, give_value)
                    if type_synonym and give_value[type_synonym] in module_synonyms:
                        # Element is module, parse it recursively
                        module.children.append(cls.parse(module, path + ':' + give_name, give_value))
                    else:
                        # Element is pin, parse it
                        module.give_pins[give_name] = Pin.parse(give_name, module, give_value)
            elif attribute_name in constraints_synonyms:
                module.constraints.update(attribute_value)
            elif attribute_name in link_synonyms:
                links.update(attribute_value)
            else:
                type_synonym = first_intersection(type_synonyms, attribute_value)
                if type_synonym in module_synonyms:
                    # Element is module, parse it recursively
                    module.children.append(cls.parse(module, path + ':' + attribute_name, attribute_value))
                else:
                    module.attributes[attribute_name] = attribute_value
        # Resolve links
        for give_pin_name in module.give_pins:
            for link_pin_name in module.give_pins[give_pin_name].links:
                if link_pin_name in module.take_pins:
                    module.links[module.give_pins[give_pin_name]] = module.take_pins[link_pin_name]
                    module.links[module.take_pins[link_pin_name]] = module.give_pins[give_pin_name]
                else:
                    # Link error, no such pin
                    print('\nLink error, no such pin:', link_pin_name, '\n')
        for take_pin_name in module.take_pins:
            for link_pin_name in module.take_pins[take_pin_name].links:
                if link_pin_name in module.give_pins:
                    module.links[module.take_pins[take_pin_name]] = module.give_pins[link_pin_name]
                    module.links[module.give_pins[link_pin_name]] = module.take_pins[take_pin_name]
                else:
                    # Link error, no such pin
                    print('\nLink error, no such pin:', link_pin_name, '\n')
        for take_pin_name in links:
            if take_pin_name in module.take_pins:
                if type(links[take_pin_name]) and links[take_pin_name] in module.give_pins:
                    module.links[module.take_pins[take_pin_name]] = module.give_pins[links[take_pin_name]]
                    module.links[module.give_pins[links[take_pin_name]]] = module.take_pins[take_pin_name]
                else:
                    # Link error, no such pin
                    print('\nLink error, no such pin:', module.links[take_pin_name], '\n')
            else:
                # Link error, no such pin
                print('\nLink error, no such pin:', take_pin_name, '\n')

        cls.parse_recurse_deep_counter -= 1
        if cls.parse_recurse_deep_counter == 0:
            # Root module post parse actions

            # Resolve all connections with children
            for module_a in chain(module.children, [module]):
                for module_b in chain(module.children, [module]):
                    if module_a != module_b:
                        module_a.connect(module_b)
        return module

    def __init__(self, parent, name, path):
        self.parent = parent
        self.name = name
        self.path = path
        self.take_pins = {}
        self.give_pins = {}
        self.attributes = {}
        self.children = []
        self.constraints = {}
        self.links = {}

    def __str__(self):
        repr = '\nModule {}: name: {}, attributes: {}'.format(self.path, self.name, self.attributes)
        for pin in self.give_pins:
            repr += '\n    ' + str(self.give_pins[pin])
        for pin in self.take_pins:
            repr += '\n    ' + str(self.take_pins[pin])
        for link in self.links:
            repr += '\n        Link: ' + link.name + ' - ' + self.links[link].name
        for child in self.children:
            repr += '\n    ' + str(child)
        return repr

    def __repr__(self):
        return self.__str__()

    def connect(self, module):
        print('Trying to connect module {} to {}'.format(self.name, module.name))
        for pin in self.take_pins:
            for pin_candidat in module.give_pins:
                # Check all constraints
                for pin_parameter in self.take_pins[pin].parameters:
                    for pin_candidat_parameter in module.give_pins[pin_candidat].parameters:
                        if pin_parameter == pin_candidat_parameter:
                            # print('    ', pin_parameter, self.take_pins[pin].parameters[pin_parameter])
                            self.take_pins[pin].connect(module.give_pins[pin_candidat])
