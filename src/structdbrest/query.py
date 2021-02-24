
from collections import defaultdict
from functools import partial
import json
import re
import time
from collections import defaultdict

import requests


import structdbrest.data_classes as data_classes


ENTRY_TYPE_KEY = "__entry_type"

composition_query_pattern = re.compile("([A-Z][a-z]?)[-]?([0-9\%])?|\\*")
common_fields = ["id"]
common_property_fields = ["NAME", "_VALUE",
                          "ORIGINAL_STRUCTURE",
                          "CALCULATOR_ID",
                          "_EXTRA_SETTINGS",
                          "TYPE_ID",
                          "CALCULATOR",
                          "COMPOSITION",
                          "TYPE",
                          "CHILDREN",
                          "STRUCTURES"
                          ]
common_entry_fields = ["COMPOSITION", "OCCUPATION", 'WYCKOFF_SITES', "MAGNETIC_MOMENTS", "CHARGES",
                       "LATTICE_VECTORS", "COORDINATES", "COORDINATES_TYPE", "NUMBER_OF_ATOMS", "NUMBER_OF_ATOMTYPES",
                       "PEARSON", "SPACEGROUP"]
common_structure_entry_fields = common_entry_fields + ["GENERICPARENT"]
common_generic_entry_fields = common_entry_fields + ["STRUKTURBERICHT", "PROTOTYPE_STRUCTURE", "PROTOTYPE_NAME"]
common_calculator_fields = ["NAME",
                            "SHORT_NAME",
                            "SETTINGS"]
common_property_type_fields = ["NAME"]

common_comparison_type_fields = ["NAME", "CODE", "DESCRIPTION", "METRICS_DESCRIPTION", "PROPERTY_TYPE_ID",
                                 "PROPERTY_TYPE"]


def db_entry_cache_decorator(make_entries_method, entries_cache):
    if not isinstance(entries_cache, defaultdict):
        new_entries_cache = defaultdict(dict)
        new_entries_cache.update(entries_cache)
        entries_cache = new_entries_cache

    def cached_method(*args, **kwargs):
        if len(args) > 0:
            entry_json = args[0]
        elif "entry_json" in kwargs:
            entry_json = kwargs["entry_json"]
        else:
            raise AttributeError("This method requires 'entry_json' argument")
        if isinstance(entry_json, dict) and ENTRY_TYPE_KEY in entry_json:
            entry_type = entry_json[ENTRY_TYPE_KEY]
            entry_id = entry_json.get("id")
            if entry_id is not None:
                if entry_id in entries_cache[entry_type]:
                    return entries_cache[entry_type][entry_id]
                else:
                    result = make_entries_method(*args, **kwargs)
                    entries_cache[entry_type][entry_id] = result
                    return result

        raise ValueError(
            "Not valid `entry_json`, has no `{ENTRY_TYPE_KEY}`={entry_json}".format(ENTRY_TYPE_KEY=ENTRY_TYPE_KEY,
                                                                                    entry_json=str(entry_json)))

    return cached_method


def del_none(d):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.

    This alters the input so you may wish to ``copy`` the dict first.
    """
    for key, value in list(d.items()):
        if value is None:
            del d[key]
        elif isinstance(value, dict):
            del_none(value)
    return d


def process_composition_query(c):
    if c == "%":
        return ('%', -1)
    finded = composition_query_pattern.findall(c)
    p_comp = finded
    p_comp = sorted(p_comp, key=lambda d: d[0])
    query = []
    asteriks_query = False
    num_of_atomtypes = 0
    for pair in p_comp:
        if len(pair) != 2:
            break
        else:
            el, quant = pair
            if quant == "":
                quant = "1"
            if el != "":
                query.append("{el}-{quant}".format(el=el, quant=quant))
                num_of_atomtypes += 1
            else:
                asteriks_query = True
    final_query = None
    if not asteriks_query:
        final_query = " ".join(query)
    else:
        num_of_atomtypes = -1
        final_query = "%" + "%".join(query) + "%"
    final_query = final_query.replace("%%", "%")
    return final_query, num_of_atomtypes



class StructDBLightRester:
    API_VERSION = "/api/v1.0/"
    COMPARATOR_URL = API_VERSION + "comparisontypes"
    PROPERTIES_URL = API_VERSION + "properties"
    GENERIC_URL = API_VERSION + "generics"
    PROPERTYTYPE_URL = API_VERSION + "propertytypes"
    CALCULATORTYPE_URL = API_VERSION + "calculatortypes"

    def __init__(self, url, token, entries_cache=None):
        self.url = url
        if self.url.endswith("/"):
            self.url = self.url[:-1]
        if not entries_cache:
            self.entries_cache = defaultdict(dict)
        else:
            self.entries_cache = entries_cache

        caching_decorator = partial(db_entry_cache_decorator, entries_cache=self.entries_cache)

        self.make_prop = caching_decorator(self.make_prop)
        self.make_structure = caching_decorator(self.make_structure)
        self.make_generic = caching_decorator(self.make_generic)
        self.make_property_type = caching_decorator(self.make_property_type)
        self.make_calculator = caching_decorator(self.make_calculator)
        self.make_comparison_type = caching_decorator(self.make_comparison_type)

        self.token = token

    def make_entry(self, entry_json, encoder_cache):
        if isinstance(entry_json, dict) and ENTRY_TYPE_KEY in entry_json:
            entry_type = entry_json[ENTRY_TYPE_KEY]
            if entry_type == "Property":
                return self.make_prop(entry_json, encoder_cache)
            elif entry_type == "StructureEntry":
                return self.make_structure(entry_json, encoder_cache)
            elif entry_type == "GenericEntry":
                return self.make_generic(entry_json, encoder_cache)
            elif entry_type == "CalculatorType":
                return self.make_calculator(entry_json, encoder_cache)
            elif entry_type == "PropertyType":
                return self.make_property_type(entry_json, encoder_cache)
            elif entry_type == "ComparisonType":
                return self.make_comparison_type(entry_json, encoder_cache)
        return entry_json

    def make_prop(self, entry_json, encoder_cache):
        entry_id = str(entry_json["id"])
        entry_json = encoder_cache['Property'][entry_id]

        type_id = entry_json["TYPE_ID"]
        #PropertyClass = property_class_mapping[type_id] if type_id in property_class_mapping else Property
        #new_prop = PropertyClass(name=entry_json["NAME"])
        new_prop = data_classes.Property()
        # new_prop.name=entry_json["NAME"]

        for k, v in entry_json.items():
            if k not in ["CHILDREN", "STRUCTURES"]:
                setattr(new_prop, k, self.make_entry(v, encoder_cache))
            else:
                setattr(new_prop, k, {})
                sub_dict = getattr(new_prop, k)
                for ch_name, ch_prop in v.items():
                    sub_dict[ch_name] = self.make_entry(ch_prop, encoder_cache)

        return new_prop

    def make_structure(self, entry_json, encoder_cache):
        entry_id = str(entry_json["id"])
        entry_json = encoder_cache['StructureEntry'][entry_id]

        new_struct = data_classes.StructureEntry()
        for k, v in entry_json.items():
            setattr(new_struct, k, self.make_entry(v, encoder_cache))
        return new_struct

    def make_generic(self, entry_json, encoder_cache):
        entry_id = str(entry_json["id"])
        entry_json = encoder_cache['GenericEntry'][entry_id]

        new_gen = data_classes.GenericEntry()
        for k, v in entry_json.items():
            setattr(new_gen, k, self.make_entry(v, encoder_cache))
        return new_gen

    def make_property_type(self, entry_json, encoder_cache):
        entry_id = str(entry_json["id"])
        entry_json = encoder_cache['PropertyType'][entry_id]

        new_gen = data_classes.PropertyType()
        for k, v in entry_json.items():
            setattr(new_gen, k, self.make_entry(v, encoder_cache))
        return new_gen

    def make_comparison_type(self, entry_json, encoder_cache):
        entry_id = str(entry_json["id"])
        entry_json = encoder_cache['ComparisonType'][entry_id]

        new_gen = data_classes.ComparisonType()
        for k, v in entry_json.items():
            setattr(new_gen, k, self.make_entry(v, encoder_cache))
        return new_gen

    def make_calculator(self, entry_json, encoder_cache):
        entry_id = str(entry_json["id"])

        entry_json = encoder_cache['CalculatorType'][entry_id]

        new_gen = data_classes.CalculatorType() #(entry_json["NAME"])
        for k, v in entry_json.items():
            setattr(new_gen, k, self.make_entry(v, encoder_cache))
        return new_gen

    def _query_db_entry_(self, query_data, url_endpoint, verbose):
        cache_state = {}
        for entry_type_name, entries_cache in self.entries_cache.items():
            cache_state[entry_type_name] = list(entries_cache.keys())
        query_data["cache_state"] = cache_state
        query_data["token"] = self.token

        query_data = json.dumps(query_data)
        start_time = time.time()
        # print("Query data = ", query_data)
        response = requests.post(self.url + url_endpoint, data=query_data, verify=False)
        stop_time = time.time()
        elapsed_time = stop_time - start_time

        if response.status_code != 200:
            raise ValueError("Invalid response (code {}): {}".format(response.status_code, response.content))
        else:
            if verbose:
                print("Response successful, size = {:.2f} kB, time = {:.2f} s".format(len(response.content) / 1024,
                                                                                      elapsed_time))
        try:
            response_dict = json.loads(response.content.decode('utf-8'))
            # print("response_dict=", response_dict)
            data_dump = response_dict["data_dump"]
            encoder_cache = response_dict["cache_dump"]
            result = []
            for entry_json in data_dump:
                # TODO: postprocess raw data
                res_prop = self.make_entry(entry_json, encoder_cache=encoder_cache)
                result.append(res_prop)
                # result.append(entry_json)
            if verbose:
                print(len(result), " entries received")
            return result
        except KeyError:
            print("Empty or invalid response")

    def query_comparators(self, property_type_name=None, comparator_name=None, verbose=True):
        query_data = dict(
            param_type=property_type_name if property_type_name else "",
            param_name=comparator_name if comparator_name else ""
        )

        result = self._query_db_entry_(query_data, self.COMPARATOR_URL, verbose)
        return result

    def query_generics(self, prototype_strukturbericht=None, prototype_name=None, verbose=True):
        query_data = dict(
            param_prototype_strukturbericht=prototype_strukturbericht if prototype_strukturbericht else "",
            param_prototype_name=prototype_name if prototype_name else "",
        )

        result = self._query_db_entry_(query_data, self.GENERIC_URL, verbose)
        return result

    def query_properties(self, property_type_name=None, property_name=None, structure_composition=None,
                       prototype_strukturbericht=None, prototype_name=None,
                       property_id=None,
                       calculator_name=None, visible_for_comparison_only=True,
                       limit=100,
                       verbose=True):
        query_data = dict(
            param_type=property_type_name if property_type_name else "",
            param_property_name=property_name if property_name else "",
            param_composition=structure_composition if structure_composition else "",
            param_prototype_strukturbericht=prototype_strukturbericht if prototype_strukturbericht else "",
            param_prototype_name=prototype_name if prototype_name else "",
            param_property_id=property_id if property_id is not None else "",
            param_calculator_name=calculator_name if calculator_name else "",
            param_visible_for_comparison_only=visible_for_comparison_only if visible_for_comparison_only is not None else "",
            param_limit=limit
        )

        result = self._query_db_entry_(query_data, self.PROPERTIES_URL, verbose)
        return result

    def query_property_types(self, propertytype_name=None, verbose=True):
        query_data = dict(
            param_propertytype_name=propertytype_name if propertytype_name else "",
        )

        result = self._query_db_entry_(query_data, self.PROPERTYTYPE_URL, verbose)
        return result

    def query_calculator_types(self, calculator_type_name=None, verbose=True):
        query_data = dict(
            param_calculator_type_name=calculator_type_name if calculator_type_name else "",
        )

        result = self._query_db_entry_(query_data, self.CALCULATORTYPE_URL, verbose)
        return result