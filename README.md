Description
===========
[VK API](https://new.vk.com/dev/methods) python wrapper library.

Installation from source
========================
```bash
git clone https://github.com/MrLokans/vk_api
cd vk_api
python setup.py install
```

Installation from PyPI
======================
Currently unavailable

Usage
=====

It is possible to make either unauthorized or authorized requests.


**Simple requests**
```python
>>> from vk_api.api import API
>>> api = API()
>>> api.api_method('wall.get', owner_id=1)
>>> api.wall.get(owner_id=1, offset=20, count=30)
```

**Authorized requests**

```python
>>> from vk_api.api import API
>>> api = API(use_settings=True) # will store access token in the file
>>> api.get_access_token() # Will open the browser, URL should be copied to prompt to obtain access token
```
