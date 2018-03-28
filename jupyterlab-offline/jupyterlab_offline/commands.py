import shutil
from os.path import join, abspath, basename, exists, dirname
from glob import glob
import os
import subprocess
import jinja2

from jupyterlab import commands

from ._version import __version__

JLAB_MIN = "0.31"
JLAB_MAX = "0.32"

NODE_MODULES = "node_modules"

LOCKFILE = "yarn.lock"
YARNRC = ".yarnrc"

STAGING = "staging"
STATIC = "static"

OFFLINE = "offline"
EXTENSIONS = "extensions"
NPM = "npm"
BASE = "base"


def get_offline_dir(app_dir=None):
    return join(app_dir or commands.get_app_dir(), OFFLINE)


def mangle_npm_name(name):
    """ Probably missing edge cases
        > TODO: find canonical npm/yarn regex
    """
    return name.replace("@", "").replace("/", "-")


def build(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    kw = dict(app_dir=app_dir, logger=logger)

    if logger:
        offline_extensions = list(glob(join(app_dir, OFFLINE, EXTENSIONS)))
        logger.info(
            "Attempting offline build for core and %s extensions:\n\t- %s",
            len(offline_extensions),
            "\n\t- ".join(offline_extensions)
        )

    populate_staging(offline=True, **kw)
    raw_install(offline=True, **kw)
    build_output = raw_build(**kw)

    if logger:
        logger.info("Build success\n%s", build_output[-500:])


def archive_extension(extension_package=None, extension_name=None,
                      extension_semver=None,
                      app_dir=None, logger=None, clean_=True):
    app_dir = app_dir or commands.get_app_dir()
    kw = dict(app_dir=app_dir, logger=logger)

    if logger:
        if extension_package is None:
            logger.info(
                "Building an offline baseline:\n\t app_dir: %s/offline/base",
                app_dir)
        else:
            logger.info(
                "Creating mirror of %s\n\tin %s/offline/extensions/%s",
                extension_package, app_dir, extension_name)

    populate_staging(**kw)

    if extension_package:
        raw_install(**kw)
        before = record_packages(**kw)
        if logger:
            logger.info("Found %s dependencies in `offline` before [%s]",
                        len(before),
                        extension_name or "base")
            logger.info("Installing %s", extension_package)
        install_extension(extension_package, extension_semver, **kw)
        populate_staging(**kw)
    else:
        stage_baseline_yarn_lock(**kw)
        before = []

    raw_install(**kw)
    after = record_packages(**kw)
    _archive(extension_name=extension_name,
             before=before,
             after=after,
             **kw)
    if clean_:
        clean(**kw)


def populate_staging(offline=False, app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    kw = dict(app_dir=app_dir, logger=logger)
    handler = commands._AppHandler(app_dir, logger)
    handler._populate_staging()
    patch_yarnrc(**kw)
    merge_mirrors(**kw)
    merge_lockfiles(offline=offline, **kw)


def merge_mirrors(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    staging = join(app_dir, STAGING, OFFLINE)
    offline = join(app_dir, OFFLINE)
    extensions = list(glob(join(offline, EXTENSIONS, "*")))
    for ext in [join(offline, BASE)] + extensions:
        packages = list(glob(join(ext, NPM, "*.tgz")))
        if logger:
            logger.info("Merging %s packages from %s cache",
                        len(packages), basename(dirname(ext)))
        for tgz in packages:
            try:
                shutil.copy2(tgz, join(staging, basename(tgz)))
            except Exception:
                pass


def merge_lockfiles(offline=False, app_dir=None, logger=None):
    """ Make $APP_DIR/yarn.lock the merged state of all installed extensions
    """
    app_dir = app_dir or commands.get_app_dir()
    offline = join(app_dir, OFFLINE)
    staging = join(app_dir, STAGING, LOCKFILE)

    base = join(offline, BASE, LOCKFILE)

    lockfiles = (
        [base] if exists(base) else []
    ) + sorted(
        list(glob(join(offline, EXTENSIONS, "*", LOCKFILE))),
        key=os.path.getsize
    )

    if len(lockfiles):
        if logger:
            logger.info("Merging %s lockfiles", len(lockfiles))

        if exists(staging):
            os.unlink(staging)
        shutil.copy2(lockfiles[0], staging)

        if len(lockfiles) > 1:
            shutil.copy2(lockfiles[1], staging)
            for i, lockfile in enumerate(lockfiles[2:]):
                if logger:
                    logger.info(
                        "(%s of %s): [%s]",
                        i + 1,
                        len(lockfiles) - 1,
                        basename(dirname(lockfile))
                    )
                try:
                    subprocess.check_output([
                        "git", "merge-file", staging, base, lockfile
                    ])
                except subprocess.CalledProcessError as err:
                    if logger:
                        logger.error("UHOH, 🙏 for merge resolution!\n%s", err)

                # trigger the conflict resolution and verify install
                if logger:
                    logger.info("Attempting to fix %s",
                                basename(dirname(lockfile)))
                raw_install(app_dir=app_dir, logger=logger, offline=offline)
                with open(staging) as fp:
                    staging_content = fp.read()
                assert ">>>>" not in staging_content, """Unresolved conflict
{}""".format(staging_content)


def patch_yarnrc(app_dir=None, logger=None):
    extra = """yarn-offline-mirror "./offline"\n"""
    app_dir = app_dir or commands.get_app_dir()
    yarnrc_path = join(app_dir, STAGING, YARNRC)
    yarnrc = ""
    if exists(yarnrc_path):
        with open(yarnrc_path) as fp:
            yarnrc = fp.read()

    if extra not in yarnrc:
        if logger:
            logger.info("Patching `staging/.yarnrc`")
        content = "{}\n# added by jupyterlab-offline\n{}".format(yarnrc, extra)
        with open(yarnrc_path, "w") as fp:
            fp.write(content)


def stage_baseline_yarn_lock(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    baseline = join(dirname(__import__("jupyterlab").__file__),
                    STAGING, LOCKFILE)
    staging = join(app_dir, STAGING, LOCKFILE)
    if exists(staging):
        if logger:
            logger.info("Removing  from `%s/staging/yarn.lock`", app_dir)
        os.unlink(staging)
    if logger:
        logger.info("Staging baseline yarn.lock to `%s/staging`", app_dir)
    shutil.copy2(baseline, staging)


def raw_build(app_dir=None, logger=None, dev_mode=False):
    app_dir = app_dir or commands.get_app_dir()
    if logger:
        logger.info("Running raw webpack in `staging`")
    return subprocess.check_output(
        ["jlpm", "build" if dev_mode else "build:prod"],
        cwd=join(app_dir, STAGING)
    )


def raw_install(app_dir=None, logger=None, offline=False):
    app_dir = app_dir or commands.get_app_dir()
    if logger:
        logger.info("Cleaning `staging/node_modules`")
    try:
        shutil.rmtree(join(app_dir, STAGING, NODE_MODULES))
    except Exception as err:
        pass
    if logger:
        logger.info("Running raw jlpm in `staging`")

    args = ["--ignore-optional", "--ignore-scripts"]

    if offline:
        args += ["--offline"]

    return subprocess.check_output(
        ["jlpm"] + args,
        cwd=join(app_dir, STAGING))


def record_packages(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    packages = list(glob(join(app_dir, STAGING, OFFLINE, "*.tgz")))
    if logger:
        logger.info("%s Packages in `staging/offline`",
                    len(packages))
    return packages


def install_extension(extension_package, extension_semver,
                      extension_name, app_dir=None,
                      logger=None):
    spec = (
        "{}@{}".format(extension_package, extension_semver)
        if extension_semver is not None
        else extension_package)
    if logger:
        logger.info("Installing `%s` to `offline/extensions/%s`",
                    extension_name, spec)
    if extension_package:
        return commands.install_extension(spec,
                                          app_dir=app_dir,
                                          logger=logger)


def _archive(extension_name, before=[], after=[], app_dir=None, logger=None):
    """ Bring along just those packages that were not present before
        and the lockfile
    """
    app_dir = app_dir or commands.get_app_dir()
    if extension_name:
        packages = set(after).difference(set(before))
        ext_path = abspath(join(app_dir, OFFLINE, EXTENSIONS,
                                extension_name))
    else:
        packages = set(after)
        ext_path = abspath(join(app_dir, OFFLINE, BASE))

    if logger:
        logger.info(
            """%s new dependencies (of %s) after [%s]""",
            len(packages),
            len(after),
            extension_name or BASE,
        )

    ext_npm = join(ext_path, NPM)

    if not exists(ext_npm):
        os.makedirs(ext_npm)

    shutil.copy2(join(app_dir, STAGING, LOCKFILE),
                 join(ext_path, LOCKFILE))
    [
        shutil.copy2(package, join(ext_npm, basename(package)))
        for package in packages
    ]


def clean(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    paths = [
        join(app_dir, path)
        for path in [STAGING, STATIC]
    ]
    if logger:
        logger.info("Cleaning out `static` and `staging`")
    return [shutil.rmtree(path) for path in paths if exists(path)]


CONDA_META_TEMPLATE = jinja2.Template("""
{% raw -%}
{% set name = "jupyterlab-offline-{% endraw %}{{ name }}{% raw %}" %}
{% set npm = "{% endraw %}{{ npm }}{% raw %}" %}
{% set version = "{% endraw %}{{ version }}{% raw %}" %}

{% set jlab_min = "{% endraw %}{{ jlab_min }}{% raw %}" %}
{% set jlab_max = "{% endraw %}{{ jlab_max }}{% raw %}" %}

package:
  name: {{ name }}
  version: {{ version }}

build:
  number: 0
  script:
    - jupyter laboffline install "{{ npm }}" "{{ version }}"

test:
  commands:
    - jupyter laboffline build
    - jupyter-labextension list

requirements:
  build:
    - jupyterlab-offline-jupyterlab-application-top >={{ jlab_min }},<{{ jlab_max }}
  run:
    - jupyterlab-offline-jupyterlab-application-top >={{ jlab_min }},<{{ jlab_max }}

about:
  home: {% endraw %}{{ home }}{% raw %}
  license: {% endraw %}{{ license }}{% raw %}
  summary: Offline assets for building {% endraw %}{{ npm }}{% raw %} for JupyterLab {{ jlab_min }}

## generated by jupyterlab_offline {% endraw %}{{ jlo_version }}{% raw %}
{%- endraw %}
""")


def scaffold_conda(extension_package, extension_name, extension_semver):
    # TODO: extract license
    # TODO: extract version if not given
    rendered = CONDA_META_TEMPLATE.render(
        name=extension_name,
        npm=extension_package,
        version=extension_semver,
        jlab_min=JLAB_MIN,
        jlab_max=JLAB_MAX,
        jlo_version=__version__
    )
    print(rendered)
