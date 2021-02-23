class DataClass:
    def __repr__(self):
        return type(self).__name__

class Property(DataClass):
    @property
    def VALUE(self):
        return self._VALUE

    @property
    def value(self):
        return self._VALUE

    def __repr__(self):
        try:
            return "Property({})".format(self.TYPE.NAME)
        except AttributeError:
            return super().__repr__()

class StructureEntry(DataClass):
    pass

class GenericEntry(DataClass):
    pass

class PropertyType(DataClass):
    pass

class ComparisonType(DataClass):
    pass

class CalculatorType(DataClass):
    pass
