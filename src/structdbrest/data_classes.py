import numpy as np
from ase.atoms import Atoms

class DataClass:
    def __repr__(self):
        return type(self).__name__

class Entry(DataClass):
   pass


class Property(DataClass):
    @property
    def VALUE(self):
        return self._VALUE

    @property
    def value(self):
        return self._VALUE

    def __repr__(self):
        try:
            type_name = ""
            if self.TYPE is not None:
                type_name = self.TYPE.NAME
            return "<Property #{id}:{type}:{composition}:{name}>".format(id=self.id, composition=self.COMPOSITION,
                                                                         type=type_name, name=self.NAME)
        except AttributeError:
            return super().__repr__()

class StructureEntry(Entry):
    def get_atoms(self, elems=None, linear_param_type=None, new_linear_param=None):
        """
        :return: ASE-like Atoms from given StructureEntry
         !NB!. Magnetic moments and charges are ignored, periodic boundary conditions are forced to True
        """
        if elems is None:
            elems = self.OCCUPATION
        # TODO Magnetic Moments and PBC correctly!
        if self.COORDINATES_TYPE == 'relative':
            atoms = Atoms(symbols=elems, cell=self.LATTICE_VECTORS, scaled_positions=np.array(self.COORDINATES))
            atoms.set_pbc(True)
        elif self.COORDINATES_TYPE == 'absolute':
            pbc = [np.linalg.norm(l) != 0 for l in self.LATTICE_VECTORS]

            atoms = Atoms(symbols=elems, cell=self.LATTICE_VECTORS,
                          positions=self.COORDINATES, pbc=pbc)
        else:
            raise RuntimeError("Unknown COORDINATES_TYPE: " + self.COORDINATES_TYPE)

        if self.MAGNETIC_MOMENTS is not None and len(self.MAGNETIC_MOMENTS) > 0:
            atoms.set_initial_magnetic_moments(self.MAGNETIC_MOMENTS)

        if self.CHARGES is not None and len(self.CHARGES) > 0:
            atoms.set_initial_charges(self.CHARGES)

        # augment with DB related fields
        if hasattr(self, "GENERICPARENT_ID"):
            atoms.GENERICPARENT_ID = self.GENERICPARENT_ID

        if hasattr(self, "GENERICPARENT"):
            atoms.GENERICPARENT = self.GENERICPARENT

        if hasattr(self, "STRUKTURBERICHT"):
            atoms.STRUKTURBERICHT = self.STRUKTURBERICHT

        return atoms

    def __repr__(self):
        return "<StructureEntry #{}:{}>".format(self.id if self.id is not None else -1, self.COMPOSITION)

class GenericEntry(Entry):
    def __repr__(self):
        return "<GenericEntry #{}:{}>".format(self.id if self.id is not None else -1, self.COMPOSITION)

class PropertyType(DataClass):
    def __repr__(self):
        return "<PropertyType #{id}:{name}>".format(id=self.id, name=self.NAME)

class ComparisonType(DataClass):
    def __repr__(self):
        return "<ComparisonType #{id}:{name}>".format(id=self.id, name=self.NAME)

class CalculatorType(DataClass):
    def __repr__(self):
        return "<CalculatorType #{id}:{name}>".format(id=self.id, name=self.NAME)
