import shutil
from os.path import join, abspath, basename, exists, dirname
from glob import glob
import os
import subprocess

from jupyterlab import commands

log_prefix = "📴"


def get_offline_dir(app_dir=None):
    return join(app_dir or commands.get_app_dir(), "offline")


def do_the_thing(extension_package=None, extension_name=None, app_dir=None,
                 logger=None, clean_=True):
    app_dir = app_dir or commands.get_app_dir()
    kw = dict(app_dir=app_dir, logger=logger)

    if logger:
        if extension_package is None:
            logger.warn(
                "%s Building an offline baseline in %s/offline/base",
                log_prefix, app_dir)
        else:
            logger.warn(
                "%s Creating mirror of %s\n\tin %s/offline/extensions/%s",
                log_prefix, extension_package, app_dir, extension_name)

    if logger:
        logger.warn("%s Running bog-standard build in %s", log_prefix, app_dir)

    populate_staging(build_first=extension_package is None, **kw)

    if extension_package:
        raw_install(**kw)
        before = record_packages(**kw)
        if logger:
            logger.warn("%s %s Mirrored dependencies before [%s]",
                        log_prefix, len(before),
                        extension_name or "BASELINE")
            logger.warn("%s Installing %s", log_prefix, extension_package)
        install_extension(extension_package, **kw)
        populate_staging(build_first=True, **kw)
    else:
        stage_baseline_yarn_lock(**kw)
        before = []

    raw_install(**kw)
    after = record_packages(**kw)
    archive(extension_name=extension_name,
            before=before,
            after=after,
            **kw)
    if clean_:
        clean(**kw)


def populate_staging(build_first=False, app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    kw = dict(app_dir=app_dir, logger=logger)
    if build_first:
        commands.build(**kw)
    patch_yarnrc(**kw)
    merge_mirrors(**kw)
    merge_lockfiles(**kw)


def merge_mirrors(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    staging = join(app_dir, "staging", "offline")
    offline = join(app_dir, "offline")
    extensions = list(glob(join(offline, "extensions", "*")))
    for ext in [join(offline, "base")] + extensions:
        packages = list(glob(join(ext, "npm", "*.tgz")))
        if logger:
            logger.warn("%s Merging %s packages from %s",
                        log_prefix, len(packages), basename(dirname(ext)))
        for tgz in packages:
            try:
                shutil.copy2(tgz, join(staging, basename(tgz)))
            except Exception:
                if logger:
                    logger.error("%s WHATEVER %s %s",
                                 log_prefix, basename(ext), tgz)


def merge_lockfiles(app_dir=None, logger=None):
    """ Make $APP_DIR/yarn.lock the merged state of all installed extensions
    """
    app_dir = app_dir or commands.get_app_dir()
    offline = join(app_dir, "offline")
    staging = join(app_dir, "staging", "yarn.lock")

    base = join(offline, "base", "yarn.lock")

    lockfiles = (
        [base] if exists(base) else []
    ) + sorted(
        list(glob(join(offline, "extensions", "*", "yarn.lock"))),
        key=os.path.getsize
    )

    if len(lockfiles):
        if logger:
            logger.warn("%s Merging %s lockfiles", log_prefix, len(lockfiles))

        if exists(staging):
            os.unlink(staging)
        shutil.copy2(lockfiles[0], staging)

        if len(lockfiles) > 1:
            for i, lockfile in enumerate(lockfiles[1:]):
                if logger:
                    logger.warn(
                        "%s %s/%s: [%s]",
                        log_prefix,
                        i,
                        len(lockfiles) - 1,
                        basename(dirname(lockfile))
                    )
                try:
                    subprocess.check_output([
                        "git", "merge-file", staging, base, lockfile
                    ])
                except subprocess.CalledProcessError as err:
                    if logger:
                        logger.error("%s UHOH, 🙏 for merge resolution...",
                                     log_prefix)

                # trigger the conflict resolution and verify install
                raw_install(app_dir=app_dir, logger=logger)
                with open(staging) as fp:
                    staging_content = fp.read()
                assert ">>>>" not in staging_content, """{} Unresolved conflict
{}""".format(log_prefix, staging_content)


def patch_yarnrc(app_dir=None, logger=None):
    extra = """yarn-offline-mirror "./offline"\n"""
    app_dir = app_dir or commands.get_app_dir()
    with open(join(app_dir, "staging", ".yarnrc")) as fp:
        yarnrc = fp.read()

    if extra not in yarnrc:
        if logger:
            logger.warn("%s patching yarnrc...", log_prefix)
        content = "{}\n# added by jupyterlab-offline\n{}".format(yarnrc, extra)
        with open(join(app_dir, "staging", ".yarnrc"), "w") as fp:
            fp.write(content)
        if logger:
            logger.warn("%s wrote yarnrc\n%s", log_prefix, content)


def stage_baseline_yarn_lock(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    baseline = join(dirname(__import__("jupyterlab").__file__),
                    "staging", "yarn.lock")
    staging = join(app_dir, "staging", "yarn.lock")
    if exists(staging):
        if logger:
            logger.warn("%s Removing yarn.lock from %s/staging",
                        log_prefix, app_dir)
        os.unlink(staging)
    if logger:
        logger.warn("%s Staging baseline yarn.lock to %s/staging",
                    log_prefix, app_dir)
    shutil.copy2(baseline, staging)


def raw_build(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    if logger:
        logger.warn("%s Running raw webpack in %s/staging",
                    log_prefix, app_dir)
    return subprocess.check_output(
        ["jlpm", "build"],
        cwd=join(app_dir, "staging")
    )


def raw_install(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    if logger:
        logger.warn("%s cleaning %s/staging/node_modules",
                    log_prefix, app_dir)
    shutil.rmtree(join(app_dir, "staging", "node_modules"))
    if logger:
        logger.warn("%s Running raw jlpm in %s/staging",
                    log_prefix, app_dir)

    args = []
    return subprocess.check_output(
        ["jlpm"] + args,
        cwd=join(app_dir, "staging"))


def record_packages(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    packages = list(glob(join(app_dir, "staging", "offline", "*.tgz")))
    if logger:
        logger.warn("%s %s Packages in %s/staging/offline",
                    log_prefix,
                    len(packages),
                    app_dir)
    return packages


def install_extension(extension_package=None, app_dir=None, logger=None):
    if extension_package:
        return commands.install_extension(extension_package,
                                          app_dir=app_dir,
                                          logger=logger)


def archive(extension_name, before=[], after=[], app_dir=None, logger=None):
    """bring along just those packages that were not present before
    """
    app_dir = app_dir or commands.get_app_dir()
    if extension_name:
        packages = set(after).difference(set(before))
        ext_path = abspath(join(app_dir, "offline", "extensions",
                                extension_name))
    else:
        packages = set(after)
        ext_path = abspath(join(app_dir, "offline", "base"))

    if logger:
        msg = ("""%s Archiving %s unique package(s) for %s"""
               """ (before: %s, after: %s)""")
        logger.warn(
            msg,
            log_prefix,
            len(packages), extension_name, len(before), len(after)
        )

    ext_npm = join(ext_path, "npm")

    if not exists(ext_npm):
        if logger:
            logger.warn("%s Creating %s", log_prefix, ext_path)
        os.makedirs(ext_npm)

    shutil.copy2(join(app_dir, "staging", "yarn.lock"),
                 join(ext_path, "yarn.lock"))

    if logger:
        logger.warn("%s Copying %s unique dependencies to %s...",
                    log_prefix,
                    len(packages),
                    ext_npm)
    [
        shutil.copy2(package, join(ext_npm, basename(package)))
        for package in packages
    ]


def clean(app_dir=None, logger=None):
    app_dir = app_dir or commands.get_app_dir()
    paths = [
        join(app_dir, path)
        for path in ["staging", "static"]
    ]
    if logger:
        logger.warn("%s Cleaning out paths:\n%s",
                    log_prefix,
                    "\n".join(paths))
    return list(map(shutil.rmtree, paths))
