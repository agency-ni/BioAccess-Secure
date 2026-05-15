"""
Lazy import utilities — charge les modules lourds (cv2, numpy, face_recognition)
uniquement à la première utilisation, pas au démarrage du serveur.

Usage:
    from core.lazy_import import lazy_module, lazy_func

    np             = lazy_module('numpy')
    cv2            = lazy_module('cv2')
    face_rec       = lazy_module('face_recognition')
    cosine_dist    = lazy_func('scipy.spatial.distance', 'cosine')

Le code existant (np.array(...), cv2.imdecode(...), etc.) continue à fonctionner
sans modification : le proxy charge le vrai module au premier accès d'attribut.
"""

import importlib


class lazy_module:
    """
    Proxy paresseux pour un module Python.
    Le module réel n'est importé que lors du premier accès à un attribut.
    """

    __slots__ = ('_name', '_mod')

    def __init__(self, name: str):
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_mod', None)

    def _load(self):
        mod = object.__getattribute__(self, '_mod')
        if mod is None:
            name = object.__getattribute__(self, '_name')
            mod = importlib.import_module(name)
            object.__setattr__(self, '_mod', mod)
        return mod

    def __getattr__(self, attr: str):
        return getattr(self._load(), attr)

    def __repr__(self):
        name = object.__getattribute__(self, '_name')
        mod = object.__getattribute__(self, '_mod')
        status = 'loaded' if mod is not None else 'not yet loaded'
        return f"<lazy_module '{name}' [{status}]>"

    def __dir__(self):
        return dir(self._load())


class lazy_func:
    """
    Proxy paresseux pour une fonction issue d'un sous-module.
    Exemple : cosine_distance = lazy_func('scipy.spatial.distance', 'cosine')
    """

    __slots__ = ('_module', '_attr', '_fn')

    def __init__(self, module: str, attr: str):
        object.__setattr__(self, '_module', module)
        object.__setattr__(self, '_attr', attr)
        object.__setattr__(self, '_fn', None)

    def _load(self):
        fn = object.__getattribute__(self, '_fn')
        if fn is None:
            mod = importlib.import_module(object.__getattribute__(self, '_module'))
            fn = getattr(mod, object.__getattribute__(self, '_attr'))
            object.__setattr__(self, '_fn', fn)
        return fn

    def __call__(self, *args, **kwargs):
        return self._load()(*args, **kwargs)

    def __repr__(self):
        m = object.__getattribute__(self, '_module')
        a = object.__getattribute__(self, '_attr')
        return f"<lazy_func '{m}.{a}'>"
