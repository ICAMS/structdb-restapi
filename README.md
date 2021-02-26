# About

This is a simple REST API interface to [atomistictools.org](http://atomistictools.org) website that allow to query the **structdb** database for 
crystallographic prototypes, structures, properties and calculators.

# Installation or update
`python setup.py install`

# Usage
You would require token to access the data.

```python
from structdbrest import StructDBLightRester
rest = StructDBLightRester(token = "YOUR_ACCESS_TOKEN")
```

Please contact Yury Lysogorskiy (yury.lysogorskiy(at)rub.de), ICAMS, Ruhr University Bochum, Germany to get the token.

See `notebooks/query-example.ipynb` for usage examples