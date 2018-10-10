
from maya import OpenMaya as oldOm


class NodeSticker(object):
    """Put custom icon on any node for display in the Maya GUI

    Currently the icon only shows up in Outliner panels (the DAG Outliner,
    Graph Editor and Dope Sheet).

    Note:
        Powered by Maya Python API 1.0, API 2.0 didn't able to do this.
        The key was the `setIcon` method in `MFnDependencyNode` class, Python
        API 2.0 didn't have that method.

    Example Usage:
        >> sticker = NodeSticker()
        >> sticker.set("pSphereShape1", "polyUnite.png")

        Remove custom icon
        >> sticker.revert("pSphereShape1")

        Custom icon displayed in GUI will not persist after scene closed, but
        the icon path wiil be saved into node's custom attribute, so next time
        we only need to call `show` to reveal custom icon in GUI.

        Reveal custom icon
        >> sticker.show()

    """

    ICON_ATTRIBUTE = "customIconPath"
    ICON_ATTR = "cuip"

    def _parse_target(self, target):
        """Internal function for type check"""
        if isinstance(target, (str, unicode)):
            target = [target]

        if not isinstance(target, (list, tuple)):
            raise TypeError("`target` should be string or list.")

        if not len(target):
            raise ValueError("No input target, selection empty.")

        return target

    def _parse_nodes(self, target):
        """Internal function for getting MFnDependencyNode"""
        mfn_nodes = list()
        sel_list = oldOm.MSelectionList()

        for path in target:
            sel_list.add(path)

        for i in range(len(target)):
            mobj = oldOm.MObject()
            sel_list.getDependNode(i, mobj)
            mfn_nodes.append(oldOm.MFnDependencyNode(mobj))

        return mfn_nodes

    def _create_attribute(self):
        """Internal function for attribute create"""
        attr = oldOm.MFnTypedAttribute()
        mattr = attr.create(self.ICON_ATTRIBUTE,
                            self.ICON_ATTR,
                            oldOm.MFnData.kString)
        return mattr

    def set(self, target, icon):
        """Associates a custom icon with the node for display in the Maya UI

        Arguments:
            target (str, list): Node name
            icon (str): icon file, must be a PNG file (.png) and may
                either be an absolute pathname or be relative to the
                `XBMLANGPATH` environment variable.

        """
        target = self._parse_target(target)
        mfn_nodes = self._parse_nodes(target)
        mattr = self._create_attribute()

        for node in mfn_nodes:
            try:
                node.setIcon(icon)
            except RuntimeError:
                raise("Not a valid icon: {!r}".format(icon))

            has_attr = node.hasAttribute(self.ICON_ATTRIBUTE)
            set_icon = icon != ""

            if set_icon:
                if not has_attr:
                    # Add attribute to save icon path
                    node.addAttribute(mattr)

                plug = node.findPlug(self.ICON_ATTRIBUTE)
                plug.setString(icon)

            elif has_attr:
                del_cmd = "deleteAttr -at {attr} {node}".format(
                    attr=self.ICON_ATTRIBUTE,
                    node=node.name()
                )
                oldOm.MGlobal.executeCommand(del_cmd)

    def revert(self, target):
        """Revert back to Node's default icon

        Arguments:
            target (str, list): Node name

        """
        self.set(target, icon="")

    def show(self):
        """Reveal custom icon from previous saved in scene

        Can use with scene open callback for auto display custom icon saved
        from previous session.

        """
        sel_list = oldOm.MSelectionList()
        ns_list = [""] + oldOm.MNamespace.getNamespaces(":", True)
        for ns in ns_list:
            if ns in (":UI", ":shared"):
                continue
            try:
                sel_list.add(ns + ":*." + self.ICON_ATTRIBUTE)
            except RuntimeError:
                pass

        for i in range(sel_list.length()):
            mobj = oldOm.MObject()
            sel_list.getDependNode(i, mobj)
            node = oldOm.MFnDependencyNode(mobj)
            plug = node.findPlug(self.ICON_ATTRIBUTE)
            icon_path = plug.asString()

            try:
                node.setIcon(icon_path)
            except RuntimeError:
                pass