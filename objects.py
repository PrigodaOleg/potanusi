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


class Element:
    @classmethod
    def get_values_from_parameter(cls, parameter):
        """
        Parses the parameter values
        There are several types of parameter values:
            Single value:       1           gpio
            List of values:     1 2 3
            Diapason of values: -1..3
            List of diapasons:  1..3 5..7
            Mixed type:         1 3..5 7
        There are several types of parameter constraints:
            Single constraint: =1   ~1
            List of single constraints: =1 =-3
            Diapason constraint: =1..3  ~5..7
        Values/constraints in lists have a logical relationship of "and"
        :param: parameter: string or list to parse
        :return: dictionary with a values and constraints
        """
        values = []
        constraints = []
        parameters = []
        if isinstance(parameter, str):
            if ' ' in parameter:
                # Complex parameter
                parameters = parameter.split(' ')
            else:
                # Simple parameter
                parameters.append(parameter)
        for param in parameters:
            if '=' == param[0]:
                # Value must be equal to param, or must be in diapason
                if '..' in param:
                    boundaries = param.split('..')
                    constraints.append((boundaries[0][1:], boundaries[-1]))
                else:
                    constraints.append((param[1:]))
            elif '~' == param[0]:
                # Value must be not equal to param, or must be out of diapason
                if '..' in param:
                    boundaries = param.split('..')
                    constraints.append([boundaries[0][1:], boundaries[-1]])
                else:
                    constraints.append([param[1:]])
            else:
                values.append(param)

        return {'values': values, 'constraints': constraints}


class Pin(Element):
    @classmethod
    def parse(cls, name, parent_module, descriptor):
        parameters = {}
        reciprocal = {}
        links = []
        scope = ''
        if descriptor:
            if type(descriptor) == str:
                links.append(descriptor)
            else:
                for pin_attribute_name, pin_attribute_value in descriptor.items():
                    if pin_attribute_name in name_synonyms:
                        name = pin_attribute_value
                    elif pin_attribute_name in reciprocal_synonyms:
                        # todo: parse
                        reciprocal = pin_attribute_value
                    elif pin_attribute_name in link_synonyms:
                        links.append(pin_attribute_value)
                    elif pin_attribute_name == 'scope':
                        assert isinstance(pin_attribute_value, str)
                        scope = {'values': pin_attribute_value}
                    else:
                        parameters[pin_attribute_name] = cls.get_values_from_parameter(pin_attribute_value)

        # If type is unknown, get type and index from name
        type_synonym = first_intersection(type_synonyms, parameters)
        if not type_synonym:
            type_synonym = type_synonyms[0]
            listed_name = name.split('_')
            if listed_name[-1].isdigit():
                parameters[type_synonym] = {'values': ['_'.join(listed_name[:-1])]}
                index_synonym = first_intersection(index_synonyms, parameters)
                if not index_synonym:
                    index_synonym = index_synonyms[0]
                    parameters[index_synonym] = {'values': [int(listed_name[-1])]}
            else:
                parameters[type_synonym] = {'values': [name]}

        # Add type constraints (types must matches for connecting)
        for type_synonym in type_synonyms:
            if type_synonym in parameters:
                for pin_type_name in parameters[type_synonym]['values']:
                    if 'constraints' not in parameters[type_synonym]:
                        parameters[type_synonym]['constraints'] = []
                    if not parameters[type_synonym]['constraints']:
                        parameters[type_synonym]['constraints'].append(pin_type_name)

        # Add module constraints to the pin
        for type_synonym in type_synonyms:
            if type_synonym in parameters:
                for pin_type_name in parameters[type_synonym]['values']:
                    if pin_type_name in parent_module.constraints:
                        for parameter_name in parent_module.constraints[pin_type_name]:
                            if parameter_name not in parameters[type_synonym]:
                                parameters[parameter_name] = {'values': [], 'constraints': []}
                            for pin_type_value in parent_module.constraints[pin_type_name][parameter_name]['values']:
                                parameters[parameter_name]['values'].append(pin_type_value)
                            for pin_type_constraint in parent_module.constraints[pin_type_name][parameter_name]['constraints']:
                                parameters[parameter_name]['constraints'].append(pin_type_constraint)

        pin = cls(parent_module, parameters)
        pin.name = name
        pin.reciprocal = reciprocal
        pin.links = links
        return pin, scope

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
        if self.is_pins_connectable(pin):
            self.connected_to.append(pin)
            pin.connected_to.append(self)

    def is_pins_connectable(self, pin):
        """
        Checks parameters for matching.
        :param: pin2: pin to check a connection possibility
        :return: True/False - connection is possible / connection is not possible
        """
        match = False
        pin1 = self
        pin2 = pin
        for _ in range(2):
            for parameter in pin1.parameters:
                if 'constraints' in pin1.parameters[parameter] and pin1.parameters[parameter]['constraints']:
                    pin1_constraints = pin1.parameters[parameter]['constraints']
                    if parameter in pin2.parameters:
                        pin2_values = pin2.parameters[parameter]['values']
                        # Compare values and constraints
                        values_is_satisfied = [False] * len(pin2_values)
                        for cnstr in pin1_constraints:
                            constraint_is_satisfied = False
                            constraint_index = 0
                            for vl in pin2_values:
                                if isinstance(cnstr, tuple):
                                    # Value must be in diapason
                                    # todo
                                    pass
                                elif isinstance(cnstr, list):
                                    # Value must NOT be in diapason
                                    # Diapason
                                    # todo
                                    pass
                                else:
                                    # Other type
                                    # The value must equal to the constraint
                                    if cnstr in vl:
                                        values_is_satisfied[constraint_index] = True if values_is_satisfied[constraint_index] is False else False
                                        constraint_is_satisfied = True if constraint_is_satisfied is False else False
                                constraint_index += 1
                            if not constraint_is_satisfied:
                                # Constraint is not satisfied
                                return False
                        if False in values_is_satisfied:
                            # At list one value out of constraints
                            return False
                    else:
                        # There are not values to compare with constraints
                        # Pins is not connectable
                        return False
                    # All constraints and values is satisfied
                    match = True
            pin2 = self
            pin1 = pin
        return match


class Module(Element):
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
                        pin, scope = Pin.parse(take_name, module, take_value)
                        module.add_pin_to_module_by_scope(pin, scope, False)
            elif attribute_name in gives_synonyms:
                for give_name, give_value in attribute_value.items():
                    type_synonym = first_intersection(type_synonyms, give_value)
                    if type_synonym and give_value[type_synonym] in module_synonyms:
                        # Element is module, parse it recursively
                        module.children.append(cls.parse(module, path + ':' + give_name, give_value))
                    else:
                        # Element is pin, parse it
                        pin, scope = Pin.parse(give_name, module, give_value)
                        module.add_pin_to_module_by_scope(pin, scope, True)
            elif attribute_name in constraints_synonyms:
                for pin_type in attribute_value:
                    module.constraints[pin_type] = {}
                    if attribute_value[pin_type]:
                        for parameter in attribute_value[pin_type]:
                            module.constraints[pin_type][parameter] =\
                                cls.get_values_from_parameter(attribute_value[pin_type][parameter])
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

        # Root module post parse actions
        if cls.parse_recurse_deep_counter == 0:
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
            repr += '\n    ->' + str(self.give_pins[pin])
        for pin in self.take_pins:
            repr += '\n    <-' + str(self.take_pins[pin])
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
            for pin_candidate in module.give_pins:
                # Check all constraints
                for pin_parameter in self.take_pins[pin].parameters:
                    for pin_candidat_parameter in module.give_pins[pin_candidate].parameters:
                        if pin_parameter == pin_candidat_parameter:
                            # print('    ', pin_parameter, self.take_pins[pin].parameters[pin_parameter])
                            self.take_pins[pin].connect(module.give_pins[pin_candidate])

    def add_pin_to_module_by_scope(self, pin, scope, is_pin_give=False):
        # Add pin to modules according scope
        module = self
        if is_pin_give:
            module.give_pins[pin.name] = pin
        else:
            module.take_pins[pin.name] = pin
        if scope:
            while module:
                if module.parent:
                    if module.name in scope['values']:
                        if is_pin_give:
                            module.give_pins[pin.name] = pin
                        else:
                            module.take_pins[pin.name] = pin
                        break
                else:
                    # It's a root module
                    if 'root' in scope['values']:
                        if is_pin_give:
                            module.give_pins[pin.name] = pin
                        else:
                            module.take_pins[pin.name] = pin
                module = module.parent
