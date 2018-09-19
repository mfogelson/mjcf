from xmltodict import unparse
import inspect
from inspect import signature


class Element(object):
    def __init__(self):
        self._attribute_names = []
        self._children = []
        self._default_args = self.get_default_args()

    def get_default_args(self):
        sig = signature(self.__class__)
        return {
            k: v.default
            for k, v in sig.parameters.items()
            if v.default is not inspect.Parameter.empty
        }

    def _xml_style_update(self, parent, child):
        """
        Update the parent dict with a new child key:value pair unless the
        key already exists in parent, then turn the key's value into a list
        and append the child value.
        """
        assert len(child.keys()) == 1
        child_key = list(child.keys())[0]
        # Turn the dict into a list when needed
        if child_key in parent:
            prev_val = parent[child_key]
            if isinstance(prev_val, list):
                parent[child_key].append(child[child_key])
            else:
                parent[child_key] = [prev_val, child[child_key]]
        else:
            parent.update(child)

        return parent

    def _stringify_value(self, val):
        """
        Values need to be in an XML/MCJF compatible format.
        """

        if isinstance(val, list):
            val = str(val).strip(("[]")).replace(",", "")
        if isinstance(val, bool):
            val = str(val).lower()

        return val

    def _is_default_value(self, value, param):
        """
        Returns True if the value is equal to the default value for this param
        """
        default = self._default_args.get(param)
        if default is not None and default == value:
            return True

        return False

    def _to_dict(self, omit_defaults=False):
        """
        Returns a dict ready for processing by xmltodict lib
        """
        element_name = self.__class__.__name__
        element_name = element_name.lower()
        outdict = {element_name: {}}
        for attr in self._attribute_names:
            v = getattr(self, attr)

            # Ignore values set to a Python None
            if v is None:
                continue
            # Default values clutter mjcf xml so strip them
            if omit_defaults and self._is_default_value(v, attr):
                continue
            # Strip underscore from protected name
            if attr == "class_":
                attr = "class"
            k = "@{}".format(attr)
            outdict[element_name][k] = self._stringify_value(v)

        for child in self._children:
            child_dict = child._to_dict()
            outdict[element_name] = self._xml_style_update(
                outdict[element_name],
                child_dict
            )

        return outdict

    def xml(self):
        """
        Returns an XML string representation of this element
        """

        outdict = self._to_dict()
        return unparse(outdict, pretty=True)

    def add_child(self, child):
        """
        Adds a child element to the list of children for this element

        TODO: Prevent or detect loops
        """
        assert isinstance(child, Element)

        self._children.append(child)

    def add_children(self, children):
        """
        Adds multiple children to the list of children for this element
        """
        [self.add_child(child) for child in children]
