"""Utility functions."""
import uuid
from copy import deepcopy
from typing import Dict

from taurus.entity.base_entity import BaseEntity
from taurus.entity.dict_serializable import DictSerializable
from taurus.entity.link_by_uid import LinkByUID
from toolz import concatv


def set_uuids(obj, name="auto"):
    """
    Recursively assign a uuid to every BaseEntity that doesn't already contain a uuid.

    This ensures that all of the pointers in the object can be replaced with LinkByUID objects
    :param obj: to recursively assign uuids to
    :param name: of the uuid to assign (default: "auto")
    :return: None
    """
    def func(base_obj):
        if len(base_obj.uids) == 0:
            base_obj.add_uid(name, str(uuid.uuid4()))
        return
    recursive_foreach(obj, func)
    return


def _substitute(thing, sub, applies, visited: Dict[int, object] = None):
    if visited is None:
        visited = {}
    if thing.__hash__ is not None and thing in visited:
        return visited[thing]
    if applies(thing):
        replacement = sub(thing)
        if thing.__hash__ is not None:
            visited[thing] = replacement
        new = _substitute(replacement, sub, applies, visited)
    elif isinstance(thing, list):
        new = [_substitute(x, sub, applies, visited) for x in thing]
    elif isinstance(thing, tuple):
        new = tuple(_substitute(x, sub, applies, visited) for x in thing)
    elif isinstance(thing, dict):
        new = {_substitute(k, sub, applies, visited): _substitute(v, sub, applies, visited)
               for k, v in thing.items()}
    elif isinstance(thing, DictSerializable):
        new_attrs = {_substitute(k, sub, applies, visited): _substitute(v, sub, applies, visited)
                     for k, v in thing.as_dict().items()}
        new = thing.from_dict(new_attrs)
    else:
        new = thing

    if thing.__hash__ is not None:
        visited[thing] = new
    if new.__hash__ is not None:
        visited[new] = new

    return new


def substitute_links(obj, native_uid=None):
    """
    Recursively replace pointers to BaseEntity with LinkByUID objects.

    This prepares the object to be serialized or written to the API.
    It is the inverse of substitute_objects.
    :param obj: target of the operation
    :param native_uid: preferred uid to use for creating LinkByUID objects (Default: None)
    """
    def make_link(entity: BaseEntity):
        if len(entity.uids) == 0:
            raise ValueError("No UID for {}".format(entity))
        elif native_uid and native_uid in entity.uids:
            return LinkByUID(native_uid, entity.uids[native_uid])
        else:
            return LinkByUID.from_entity(entity)

    return _substitute(obj, sub=make_link,
                       applies=lambda o: o is not obj and isinstance(o, BaseEntity))


def substitute_objects(obj, index):
    """
    Recursively replace LinkByUID objects with pointers to the objects with that UID in the index.

    This prepares the object to be used after being deserialized.
    It is the inverse of substitute_links.
    :param obj: target of the operation
    :param index: containing the objects that the uids point to
    """
    return _substitute(obj,
                       sub=lambda l: index.get((l.scope.lower(), l.id), l),
                       applies=lambda o: isinstance(o, LinkByUID))


def flatten(obj):
    """
    Flatten a BaseEntity into a list of objects connected by LinkByUID objects.

    This is a composite operation the amounts to:
      - Making sure at least one uid is set in each BaseEntity in scope
      - Getting a list of unique objects contained in the scope
      - Substituting the pointers in those objects with LinkByUID objects
    :param obj: defining the scope of the flatten
    :return: a list of BaseEntity with LinkByUIDs to any BaseEntity members
    """
    # The ids should be set in the actual object so they are consistent
    set_uuids(obj)

    # TODO: remove this
    # make a copy before we substitute the pointers for links
    copy = deepcopy(obj)

    # list of uids that we've seen, to avoid returning duplicates
    known_uids = set()

    def _flatten(base_obj):
        to_return = []
        # get all the uids of this object
        uids = list(base_obj.uids.items())

        # if none of the uids are known, then its a new object and we should return it
        if not any(uid in known_uids for uid in uids):
            to_return = [base_obj]

        # add all of the uids of this object into the known uid list
        for uid in uids:
            known_uids.add(uid)

        return to_return

    res = recursive_flatmap(copy, _flatten)
    return [substitute_links(x) for x in res]


def recursive_foreach(obj, func, apply_first=False, seen=None):
    """
    Apply a function recursively to each BaseEntity object.

    Only objects of type BaseEntity will have the function applied, but the recursion will walk
    through all objects.  For example, BaseEntity -> list -> BaseEntity will have func applied
    to both base entities.

    :param obj: target of the operation
    :param func: to apply to each contained BaseEntity
    :param apply_first: whether to apply the func before applying it to members (default: false)
    :param seen: set of seen objects (default=None).  DON'T PASS THIS!!!
    :return: None
    """
    if seen is None:
        seen = set({})
    if obj.__hash__ is not None:
        if obj in seen:
            return
        else:
            seen.add(obj)

    if apply_first and isinstance(obj, BaseEntity):
        func(obj)

    if isinstance(obj, (list, tuple)):
        for i, x in enumerate(obj):
            recursive_foreach(x, func, apply_first, seen)
    elif isinstance(obj, dict):
        for x in concatv(obj.keys(), obj.values()):
            recursive_foreach(x, func, apply_first, seen)
    elif isinstance(obj, DictSerializable):
        for k, x in obj.__dict__.items():
            recursive_foreach(x, func, apply_first, seen)

    if isinstance(obj, BaseEntity) and not apply_first:
        func(obj)

    return


def recursive_flatmap(obj, func, seen=None):
    """
    Recursively apply and accumulate a list-valued function to BaseEntity members.

    :param obj: target of the operation
    :param func: function to apply; must be list-valued
    :param seen: set of seen objects (default=None).  DON'T PASS THIS
    :return: a list of accumulated return values
    """
    res = []

    if seen is None:
        seen = set({})
    if obj.__hash__ is not None:
        if obj in seen:
            return res
        else:
            seen.add(obj)

    if isinstance(obj, (list, tuple)):
        for i, x in enumerate(obj):
            if isinstance(x, BaseEntity):
                res.extend(recursive_flatmap(x, func, seen))
                res.extend(func(x))
            else:
                res.extend(recursive_flatmap(x, func, seen))
    elif isinstance(obj, dict):
        for x in concatv(obj.keys(), obj.values()):
            if isinstance(x, BaseEntity):
                res.extend(recursive_flatmap(x, func, seen))
                res.extend(func(x))
            else:
                res.extend(recursive_flatmap(x, func, seen))
    elif isinstance(obj, DictSerializable):
        for k, x in sorted(obj.__dict__.items()):
            if isinstance(obj, BaseEntity) and k in obj.skip:
                continue
            if isinstance(x, BaseEntity):
                res.extend(recursive_flatmap(x, func, seen))
                res.extend(func(x))
            else:
                res.extend(recursive_flatmap(x, func, seen))
    return res
