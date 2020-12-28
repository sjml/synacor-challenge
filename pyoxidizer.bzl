def make_dist():
    return default_python_distribution(
        python_version="3.8"
    )

def make_exe(dist):
    policy = dist.make_python_packaging_policy()
    policy.extension_module_filter = "all"
    # policy.file_scanner_classify_files = True
    policy.allow_files = True
    policy.file_scanner_emit_files = True
    # policy.include_classified_resources = True
    policy.resources_location = "in-memory"

    python_config = dist.make_python_interpreter_config()
    python_config.run_module = 'game'

    exe = dist.to_python_executable(
        name="synacor-challenge",
        packaging_policy=policy,
        config=python_config,
    )
    exe.add_python_resources(exe.read_package_root(
        path=".",
        packages=["game", "machine", "datafiles"],
    ))
    exe.add_python_resources(exe.pip_download(
        ["-r", "requirements.txt"]
    ))

    return exe

def make_embedded_resources(exe):
    return exe.to_embedded_resources()

def make_install(exe):
    files = FileManifest()
    files.add_python_resource(".", exe)
    return files

register_target("dist", make_dist)
register_target("exe", make_exe, depends=["dist"], default=True)
register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
register_target("install", make_install, depends=["exe"])

resolve_targets()

PYOXIDIZER_VERSION = "0.10.3"
PYOXIDIZER_COMMIT = "UNKNOWN"
