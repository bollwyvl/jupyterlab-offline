from jupyter_core.application import JupyterApp, base_aliases, base_flags
from traitlets import Unicode, Bool

from . import commands

version = "0.1.0"


# utility function
def _subcommandify(**subcommands):
    return dict([
        (k, (v, v.description.strip().splitlines()[0]))
        for k, v in subcommands.items()
    ])


install_aliases = dict(base_aliases)
install_aliases["app-dir"] = "OfflineInstallApp.app_dir"
install_aliases["extension"] = "OfflineInstallApp.extension_package"
install_aliases["semver"] = "OfflineInstallApp.extension_semver"
install_aliases["name"] = "OfflineInstallApp.extension_name"
install_aliases["clean"] = "OfflineInstallApp.clean"

install_flags = dict(base_flags)
install_flags["baseline"] = (
    {"OfflineInstallApp": {"baseline": True}},
    "Do a baseline build with shipped yarn.lock and no extensions"
)


class OfflineInstallApp(JupyterApp):
    version = version
    description = """
    Store an npm-installable extension and its dependencies (network required)

    The resulting assets (yarn.lock and dependencies as .tgz files) will be
    available after the build, suitable for packaging.
    """

    aliases = install_aliases
    flags = install_flags

    app_dir = Unicode(
        None,
        config=True,
        allow_none=True,
        help="The app directory to build in")

    extension_package = Unicode(
        None,
        allow_none=True,
        config=True,
        help="The npm-installable (@scope)/name")

    extension_semver = Unicode(
        None,
        allow_none=True,
        config=True,
        help="A simple semver string for the npm package")

    extension_name = Unicode(
        None,
        allow_none=True,
        config=True,
        help="A simple semver string for the npm package, defaults to mangled"
             " npm name")

    baseline = Bool(
        False,
        config=True,
        help="Whether to do a baseline build (vs a base + extensions build)"
    )

    clean = Bool(
        True,
        config=True,
        help="Whether to clean contentious directories after build")

    def parse_command_line(self, argv=None):
        super(OfflineInstallApp, self).parse_command_line(argv)

        if self.baseline:
            self.extension_package = None
            self.extension_name = None
            self.extension_semver = None
            return

        if len(self.extra_args) == 1:
            self.extension_package = self.extra_args[0]
        elif len(self.extra_args) == 2:
            self.extension_package, self.extension_semver = self.extra_args

        if self.baseline is None and self.extension_package is None:
            raise ValueError(
                "Either specify:\n\n"
                "\tjupyter laboffline install @scope/extension 0.0.0\n"
                "# or (advanced)\n"
                "\tjupyter laboffline install --baseline\n"
            )

        if self.extension_name is None:
            self.extension_name = commands.mangle_npm_name(
                self.extension_package
            )

    def start(self):
        kwargs = dict(
            app_dir=self.app_dir,
            extension_name=self.extension_name,
            extension_package=self.extension_package,
            extension_semver=self.extension_semver,
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
            logger=self.log,
        )
        commands.build(**kwargs)


conda_aliases = dict(base_aliases)
conda_aliases["extension"] = "ScaffoldCondaApp.extension_package"
conda_aliases["name"] = "ScaffoldCondaApp.extension_name"
conda_aliases["semver"] = "ScaffoldCondaApp.extension_semver"


class ScaffoldCondaApp(JupyterApp):
    version = version
    description = """
    Generate a conda-forge-style conda recipe
    """

    aliases = conda_aliases

    extension_package = Unicode(
        config=True,
        help="The npm-installable (@scope)/name")

    extension_name = Unicode(
        config=True,
        help="An on-disk friendly name derived from the extension")

    extension_semver = Unicode(
        config=True,
        help="A simple semver string (no comparators)")

    def parse_command_line(self, argv=None):
        super(ScaffoldCondaApp, self).parse_command_line(argv)

        if len(self.extra_args) == 2:
            self.extension_package, self.extension_semver = self.extra_args
            self.extension_name = commands.mangle_npm_name(
                self.extension_package)

        if self.extension_package is None:
            raise ValueError(
                "Usage:\n\n"
                "\tjupyter laboffline scaffold conda @scope/extension 0.0.0\n"
            )

    def start(self):
        commands.scaffold_conda(extension_package=self.extension_package,
                                extension_name=self.extension_name,
                                extension_semver=self.extension_semver)


class OfflineScaffoldApp(JupyterApp):
    version = version
    description = """
    Bootstrap package manager solutions
    """

    subcommands = _subcommandify(conda=ScaffoldCondaApp)


class OfflineApp(JupyterApp):
    version = version
    description = """
    Utilities for offline JupyterLab building
    """

    subcommands = _subcommandify(
        build=OfflineBuildApp,
        scaffold=OfflineScaffoldApp,
        install=OfflineInstallApp,
    )


main = launch_new_instance = OfflineApp.launch_instance

if __name__ == '__main__':
    main()
