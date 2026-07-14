# Python API reference

The whole surface is the {class}`~crowdsky_client.Client` class plus the
{class}`~crowdsky_client.CrowdSkyError` exception. These names are stable — CrowdSci modules and the
Zeus runner code against them.

```python
from crowdsky_client import Client, CrowdSkyError
```

## `Client`

```{eval-rst}
.. autoclass:: crowdsky_client.Client
   :members:
   :member-order: bysource
```

## Exceptions

```{eval-rst}
.. autoexception:: crowdsky_client.CrowdSkyError
   :members:
```

## Module constants

```{eval-rst}
.. autodata:: crowdsky_client.HEALPIX_NSIDE
.. autodata:: crowdsky_client.HEALPIX_ORDER
```

`CrowdSkyClient` is kept as an alias of `Client` for backward compatibility with earlier
CrowdSci-side code.
