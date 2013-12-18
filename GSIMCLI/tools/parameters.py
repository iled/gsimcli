# -*- coding: utf-8 -*-
'''
Created on 6 de Dez de 2013

@author: julio
'''


class ParametersFile:
    """Base class to construct a ParametersClass.

    """

    def __init__(self, sep, par_set=str(), par_file=str(), text=list(),
                 real_n=list(), int_n=list(), boolean=list(), optional=list(),
                 parpath=None, order=None):
        """Constructor.

        """
        self.path = parpath
        self.sep = sep
        self.par_set = par_set
        self.par_file = par_file
        self.text = text
        self.real = real_n
        self.int = int_n
        self.boolean = boolean
        self.optional = optional
        self.fields = self.text + self.real + self.int + self.boolean
        self.order = order
        if order and len(order) != len(self.fields + self.optional):
            raise ValueError('Incomplete list of ordered fields.')
        if parpath:
            self.load(parpath)

    def template(self, par_path):
        """Write a parameter file with the template to follow, which must have
        been defined as a docstring.

        """
        self.path = par_path
        par_file = open(par_path, 'w')
        lines = self.__doc__.splitlines()
        for line in lines:
            par_file.write(line.strip() + '\n')
        par_file.close()

    def load(self, par_path):
        """Load a parameter file.

        TODO: load ordered
        """
        self.path = par_path
        with open(self.path) as fid:
            lines = fid.readlines()
        checklist = list(self.fields)

        for line in lines:
            field = line.split(self.sep)[0]
            if field in self.fields or field in self.optional:
                value = line.split(self.sep)[1]
                if field in self.text:
                    setattr(self, field, value.strip())
                    checklist.remove(field)
                elif field in self.real:
                    setattr(self, field, float(value))
                    checklist.remove(field)
                elif field in self.int:
                    setattr(self, field, int(value))
                    checklist.remove(field)
                elif field in self.boolean:
                    if value.strip().lower() == 'y':
                        setattr(self, field, True)
                    else:
                        setattr(self, field, False)
                    checklist.remove(field)
                else:
                    setattr(self, field, value.strip())

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
                if field in self.text:
                    par.write(field + self.sep + ' ' + value + '\n')
                elif field in self.real or field in self.int:
                    par.write(field + self.sep + ' ' + str(value) + '\n')
                elif field in self.boolean:
                    if value:
                        value = 'y'
                    else:
                        value = 'n'
                    par.write(field + self.sep + ' ' + value + '\n')
                else:
                    value = getattr(self, field)
                    par.write(field + self.sep + ' ' + value + '\n')
        par.close()

    def update(self, fields, values, save=False, par_path=None):
        """Updates a list of existing fields with the corresponding values.

        """
        for i, field in enumerate(fields):
            # if hasattr(self, field):
            if field in self.order:
                setattr(self, field, values[i])
        if save:
            self.save(par_path)
