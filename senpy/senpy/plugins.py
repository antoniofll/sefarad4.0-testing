
import inspect
import os.path
import shelve
import logging
import ConfigParser
from .models import Response, Leaf

logger = logging.getLogger(__name__)

PARAMS = {
    "input": {
        "@id": "input",
        "aliases": ["i", "input"],
        "required": True,
        "help": "Input text"
    },
    "informat": {
        "@id": "informat",
        "aliases": ["f", "informat"],
        "required": False,
        "default": "text",
        "options": ["turtle", "text"],
    },
    "intype": {
        "@id": "intype",
        "aliases": ["intype", "t"],
        "required": False,
        "default": "direct",
        "options": ["direct", "url", "file"],
    },
    "outformat": {
        "@id": "outformat",
        "aliases": ["outformat", "o"],
        "default": "json-ld",
        "required": False,
        "options": ["json-ld"],
    },
    "language": {
        "@id": "language",
        "aliases": ["language", "l"],
        "required": False,
    },
    "prefix": {
        "@id": "prefix",
        "aliases": ["prefix", "p"],
        "required": True,
        "default": "",
    },
    "urischeme": {
        "@id": "urischeme",
        "aliases": ["urischeme", "u"],
        "required": False,
        "default": "RFC5147String",
        "options": "RFC5147String"
    },
}


class SenpyPlugin(Leaf):
    _context = Leaf.get_context(Response._context)
    _frame = {"@context": _context,
              "name": {},
              "extra_params": {"@container": "@index"},
              "@explicit": True,
              "version": {},
              "repo": None,
              "is_activated": {},
              "params": None,
              }

    def __init__(self, info=None):
        if not info:
            raise ValueError(("You need to provide configuration"
                              "information for the plugin."))
        logger.debug("Initialising {}".format(info))
        super(SenpyPlugin, self).__init__()
        self.name = info["name"]
        self.version = info["version"]
        self.id = "{}_{}".format(self.name, self.version)
        self.params = info.get("params", PARAMS.copy())
        if "@id" not in self.params:
            self.params["@id"] = "params_%s" % self.id
        self.extra_params = info.get("extra_params", {})
        self.params.update(self.extra_params.copy())
        if "@id" not in self.extra_params:
            self.extra_params["@id"] = "extra_params_%s" % self.id
        self.is_activated = False
        self._info = info

    def get_folder(self):
        return os.path.dirname(inspect.getfile(self.__class__))

    def analyse(self, *args, **kwargs):
        logger.debug("Analysing with: {} {}".format(self.name, self.version))
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass

    def jsonld(self, parameters=False, *args, **kwargs):
        nframe = kwargs.pop("frame", self._frame)
        if parameters:
            nframe = nframe.copy()
            nframe["params"] = {}
        return super(SenpyPlugin, self).jsonld(frame=nframe, *args, **kwargs)

    @property
    def id(self):
        return "{}_{}".format(self.name, self.version)

    def __del__(self):
        ''' Destructor, to make sure all the resources are freed '''
        self.deactivate()

class SentimentPlugin(SenpyPlugin):

    def __init__(self, info, *args, **kwargs):
        super(SentimentPlugin, self).__init__(info, *args, **kwargs)
        self.minPolarityValue = float(info.get("minPolarityValue", 0))
        self.maxPolarityValue = float(info.get("maxPolarityValue", 1))


class EmotionPlugin(SenpyPlugin):

    def __init__(self, info, *args, **kwargs):
        resp = super(EmotionPlugin, self).__init__(info, *args, **kwargs)
        self.minEmotionValue = float(info.get("minEmotionValue", 0))
        self.maxEmotionValue = float(info.get("maxEmotionValue", 0))


class ShelfMixin(object):

    @property
    def sh(self):
        if not hasattr(self, '_sh') or not self._sh:
            self._sh = shelve.open(self.shelf_file, writeback=True)
        return self._sh

    @sh.deleter
    def sh(self):
        if os.path.isfile(self.shelf_file):
            os.remove(self.shelf_file)

    @property
    def shelf_file(self):
        if not hasattr(self, '_shelf_file') or not self._shelf_file:
            if hasattr(self, '_info') and 'shelf_file' in self._info:
                self._shelf_file = self._info['shelf_file']
            else:
                self._shelf_file = os.path.join(self.get_folder(), self.name + '.db')
        return self._shelf_file 

    def close(self):
        self.sh.close()
        del(self._sh)
