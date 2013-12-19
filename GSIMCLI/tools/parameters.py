# -*- coding: utf-8 -*-
'''
Created on 6 de Dez de 2013

@author: julio
'''


class ParametersFile:
    """Base class to construct a ParametersClass.
    
    Each parameter is defined by the following pair:
        - field: the name of the parameter which will be used both as an
                 attribute of this class, and;
        - value: which is the value of that same parameter.
        
    Fields are separated into lists of predetermined types: str (text), float
    (real_n), int (int_n) and bool (boolean).
    
    Fields can be mandatory or optional (opt_).
    
    Fields are separated from values with a given separator (field_sep). Values
    can be a single value or a list of values, which are separated with yet
    another given separator (values_sep).
    
    """

    def __init__(self, field_sep, value_sep, par_set=str(), par_file=str(),
                 text=list(), real_n=list(), int_n=list(), boolean=list(),
                 opt_text=list(), opt_real=list(), opt_int=list(),
                 opt_boolean=list(), parpath=None, order=None):
        """Constructor.

        """
        self.path = parpath
        self.field_sep = field_sep
        self.value_sep = value_sep
        self.par_set = par_set
        self.par_file = par_file
        self.text = text
        self.real = real_n
        self.int = int_n
        self.boolean = boolean
        self.opt_text = opt_text
        self.opt_real = opt_real
        self.opt_int = opt_int
        self.opt_boolean = opt_boolean
        self.optional = (self.opt_text + self.opt_real + self.opt_int
                         + self.opt_boolean)
        self.fields = self.text + self.real + self.int + self.boolean
        self.order = order
        if order and len(order) != len(self.fields + self.optional):
            raise ValueError('Incomplete list of ordered fields.')
        if parpath:
            self.load(parpath)

    def template(self, par_path):
        """Write a parameter file with the template to follow, which must have
        been defined in the docstring.

        """
        self.path = par_path
        par_file = open(par_path, 'w')
        lines = self.__doc__.splitlines()
        for line in lines:
            par_file.write(line.strip() + '\n')
        par_file.close()

    def set_field(self, field, value):
        """Create or update the value of an attr called field, given the
        desired object type.

        """
        if field in self.text + self.opt_text:
            setattr(self, field, _split(value, str.strip,
                                        self.value_sep))
        elif field in self.real + self.opt_real:
            setattr(self, field, _split(value, float, self.value_sep))
        elif field in self.int + self.opt_int:
            setattr(self, field, _split(value, int, self.value_sep))
        elif field in self.boolean + self.opt_boolean:
            if value.strip().lower() == 'y':
                setattr(self, field, True)
            else:
                setattr(self, field, False)
        else:
            setattr(self, field, value.strip())

    def load(self, par_path):
        """Load a parameter file.

        TODO: load ordered
        """
        self.path = par_path
        with open(self.path) as fid:
            lines = fid.readlines()
        checklist = list(self.fields)

        for line in lines:
            field = line.split(self.field_sep)[0]
            if field in self.fields + self.optional:
                value = line.split(self.field_sep)[1]
                self.set_field(field, value)
                if field in self.fields:
                    checklist.remove(field)
        if checklist:
            raise AttributeError('There are missing parameters: {}.'
                                 .format(', '.join(map(str, checklist))))

    def save(self, par_path=None):
        """Write the parameters file.

        """
        if not par_path:
            par_path = self.path
        else:
            self.path = par_path
        par = open(par_path, 'w')
        par.write('·' * (25 + len(self.par_set)) + '\n')
        par.write('·····  {} parameters  ·····\n'.format(self.par_set))
        par.write('·' * (25 + len(self.par_set)) + '\n')
        if self.order:
            fields = self.order
        else:
            fields = self.fields + self.optional
        for field in fields:
            if hasattr(self, field):
                value = getattr(self, field)
                if field in (self.text + self.opt_text + self.real + self.int
                             + self.opt_real + self.opt_int):
                    par.write(field + self.field_sep + ' '
                              + _join(value, self.value_sep) + '\n')
                elif field in self.boolean + self.opt_boolean:
                    if value:
                        value = 'y'
                    else:
                        value = 'n'
                    par.write(field + self.field_sep + ' ' + value + '\n')
        par.close()

    def update(self, fields, values, save=False, par_path=None):
        """Updates a list of existing fields with the corresponding values.

        """
        for i, field in enumerate(fields):
            if field in self.fields + self.optional:
                self.set_field(field, values[i])
        if save:
            self.save(par_path)


def _split(string, to_type, sep):
    """Convert a string into a give type, returning a single converted value or
    a list of converted values.

    """
    if type(string) == str:
        items = map(to_type, string.split(sep))
    else:
        items = map(to_type, [string])
    try:
        if len(items) == 1:
            return items[0]
        else:
            return items
    except:
        pass


def _join(items, sep):
    """Convert a list of items or a single item into a string, separating items
    with the given sep.

    """
    if type(items) == list:
        return (sep + ' ').join(map(str, items))
    else:
        return str(items)
