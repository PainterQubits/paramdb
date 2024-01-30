"""Keys for special properties in dictionary representations of parameter data."""

CLASS_NAME_KEY = "__type"
"""
Dictionary key corresponding to the parameter class name when :py:meth:`.ParamDB.load`
or :py:meth:`.ParamDB.commit_history_with_data` is called with ``load_classes`` as
False.
"""

PARAMLIST_ITEMS_KEY = "__items"
"""
Dictionary key corresponding to the list of items in the dictionary representation of a
:py:class:`.ParamList` object.
"""

LAST_UPDATED_KEY = "__last_updated"
"""
Dictionary key corresponding to the last updated time in the dictionary representation
of a :py:class:`.Param` object.
"""
