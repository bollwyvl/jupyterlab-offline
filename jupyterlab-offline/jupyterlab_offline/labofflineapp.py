from jupyter_core.application import JupyterApp, base_aliases
from traitlets import Unicode

from .commands import do_the_thing

version = "0.1.0"

offline_aliases = dict(base_aliases)
offline_aliases["app-dir"] = "LabOfflineApp.app_dir"
offline_aliases["extension"] = "LabOfflineApp.extension"
offline_aliases["name"] = "LabOfflineApp.name"


class LabOfflineApp(JupyterApp):
    version = version
    description = """
    Utilities for offline JupyterLab building
    """

    aliases = offline_aliases

    app_dir = Unicode(
        None,
        config=True,
        allow_none=True,
        help="The app directory to build in")

    extension = Unicode(
        None,
        allow_none=True,
        config=True,
        help="The npm-installable (@scope)/name")

    name = Unicode(
        None,
        allow_none=True,
        config=True,
        help="An on-disk friendly name derived from the extension")

    def start(self):
        kwargs = dict(
            app_dir=self.app_dir,
            extension_name=self.name,
            extension_package=self.extension,
            logger=self.log
        )
        do_the_thing(**kwargs)


main = launch_new_instance = LabOfflineApp.launch_instance

if __name__ == '__main__':
    main()
