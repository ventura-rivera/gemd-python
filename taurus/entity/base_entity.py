"""Base class for all entities."""
from taurus.entity.dict_serializable import DictSerializable
from taurus.entity.case_insensitive_dict import CaseInsensitiveDict


class BaseEntity(DictSerializable):
    """
    Base class for any entity, which includes objects and templates.

    Parameters
    ----------
    uids: Map[str, str]
        A collection of
        `unique IDs <https://citrineinformatics.github.io/taurus-documentation/
        specification/unique-identifiers/>`_.
    tags: List[str]
        `Tags <https://citrineinformatics.github.io/taurus-documentation/specification/tags/>`_
        are hierarchical strings that store information about an entity and can be used
        for discoverability.

    """

    typ = "base"

    def __init__(self, uids, tags):
        self._tags = None
        self.tags = tags

        self._uids = None
        self.uids = uids

    def content_hash(self):
        """A hash of the object's content."""
        return str(sorted(list(self.__dict__.items())))

    @property
    def tags(self):
        """Get the tags."""
        return self._tags

    @tags.setter
    def tags(self, tags):
        if tags is None:
            self._tags = []
        elif isinstance(tags, list):
            self._tags = tags
        else:
            self._tags = [tags]

    @property
    def uids(self):
        """Get the uids."""
        return self._uids

    @uids.setter
    def uids(self, uids):
        if uids is None:
            self._uids = CaseInsensitiveDict()
        elif isinstance(uids, dict):
            self._uids = CaseInsensitiveDict(**uids)
        else:
            self._uids = CaseInsensitiveDict(**{uids[0]: uids[1]})

    def add_uid(self, scope, uid):
        """
        Add a uid.

        Parameters
        ----------
        scope: str
            scope of the uid
        uid: str
            Unique identifier

        """
        self.uids[scope] = uid