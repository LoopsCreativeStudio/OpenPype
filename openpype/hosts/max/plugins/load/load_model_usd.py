import os

from openpype.hosts.max.api import lib
from openpype.hosts.max.api.lib import unique_namespace
from openpype.hosts.max.api.lib import maintained_selection
from openpype.hosts.max.api.pipeline import (
    containerise,
    import_custom_attribute_data,
    update_custom_attribute_data
)
from openpype.pipeline import get_representation_path, load


class ModelUSDLoader(load.LoaderPlugin):
    """Loading model with the USD loader."""

    families = ["model"]
    label = "Load Model(USD)"
    representations = ["usda"]
    order = -10
    icon = "code-fork"
    color = "orange"

    def load(self, context, name=None, namespace=None, data=None):
        from pymxs import runtime as rt

        # asset_filepath
        filepath = os.path.normpath(self.filepath_from_context(context))
        import_options = rt.USDImporter.CreateOptions()
        base_filename = os.path.basename(filepath)
        filename, ext = os.path.splitext(base_filename)
        log_filepath = filepath.replace(ext, "txt")

        rt.LogPath = log_filepath
        rt.LogLevel = rt.Name("info")
        rt.USDImporter.importFile(filepath,
                                  importOptions=import_options)
        asset = rt.GetNodeByName(name)

        import_custom_attribute_data(asset, asset.Children)

        namespace = unique_namespace(
            name + "_",
            suffix="_",
        )

        return containerise(
            name, [asset], context,
            namespace, loader=self.__class__.__name__)

    def update(self, container, representation):
        from pymxs import runtime as rt

        path = get_representation_path(representation)
        node_name = container["instance_node"]
        node = rt.GetNodeByName(node_name)
        for n in node.Children:
            for r in n.Children:
                rt.Delete(r)
            rt.Delete(n)
        container_name = node_name.split(":")[-1]
        param_container, _ = container_name.split("_")

        import_options = rt.USDImporter.CreateOptions()
        base_filename = os.path.basename(path)
        _, ext = os.path.splitext(base_filename)
        log_filepath = path.replace(ext, "txt")

        rt.LogPath = log_filepath
        rt.LogLevel = rt.Name("info")
        rt.USDImporter.importFile(
            path, importOptions=import_options)

        asset = rt.GetNodeByName(param_container)
        asset.Parent = node
        for children in node.Children:
            if rt.classOf(children) == rt.Container:
                if children.name == param_container:
                    update_custom_attribute_data(
                        asset, asset.Children)

        with maintained_selection():
            rt.Select(node)

        lib.imprint(node_name, {
            "representation": str(representation["_id"])
        })

    def switch(self, container, representation):
        self.update(container, representation)

    def remove(self, container):
        from pymxs import runtime as rt

        node = rt.GetNodeByName(container["instance_node"])
        rt.Delete(node)
