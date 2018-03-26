from jupyter_core.application import JupyterApp, base_aliases
from traitlets import Unicode, Bool

from . import commands

version = "0.1.0"

dependency_aliases = dict(base_aliases)
dependency_aliases["app-dir"] = "OfflineDependenciesApp.app_dir"
dependency_aliases["extension"] = "OfflineDependenciesApp.extension"
dependency_aliases["name"] = "OfflineDependenciesApp.name"
dependency_aliases["clean"] = "OfflineDependenciesApp.clean"


class OfflineDependenciesApp(JupyterApp):
    version = version
    description = """
    Store an npm-installable extension and its dependencies
    """

    aliases = dependency_aliases

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

    clean = Bool(
        True,
        config=True,
        help="Whether to clean contentious directories after build")

    def start(self):
        kwargs = dict(
            app_dir=self.app_dir,
            extension_name=self.name,
            extension_package=self.extension,
            clean_=self.clean,
            logger=self.log
        )
        commands.archive_extension(**kwargs)


build_aliases = dict(base_aliases)
build_aliases["app-dir"] = "OfflineBuildApp.app_dir"


class OfflineBuildApp(JupyterApp):
    version = version
    description = """
    Use a populated offline folder to perform an offline build
    """

    aliases = build_aliases

    app_dir = Unicode(
        None,
        config=True,
        allow_none=True,
        help="The app directory to build in")

    def start(self):
        kwargs = dict(
            app_dir=self.app_dir,
        )
        commands.build(**kwargs)


class OfflineApp(JupyterApp):
    version = version
    description = """
    Utilities for offline JupyterLab building
    """

    subcommands = dict(
        archive=(
            OfflineDependenciesApp,
            OfflineDependenciesApp.description.splitlines()[0]),
        build=(
            OfflineBuildApp,
            OfflineBuildApp.description.splitlines()[0]),
    )


main = launch_new_instance = OfflineApp.launch_instance

if __name__ == '__main__':
    main()
