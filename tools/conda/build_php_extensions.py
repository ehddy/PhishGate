#!/usr/bin/env python3
"""Build PHP 7.4 extensions omitted by conda-forge's PHP package."""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path


PHP_VERSION = "7.4.27"
PHP_SOURCE_SHA256 = "564fd5bc9850370db0cb4058d9087f2f40177fa4921ce698a375416db9ab43ca"
PHP_SOURCE_URL = f"https://www.php.net/distributions/php-{PHP_VERSION}.tar.gz"
EXTENSIONS = {
    "curl": {
        "configure": "--with-curl={prefix}",
        "functions": ("curl_version", "curl_init", "curl_setopt"),
    },
    "zlib": {
        "configure": "--with-zlib={prefix}",
        "functions": ("gzinflate", "gzdecode", "gzuncompress"),
    },
}


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        print(result.stdout, file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, command)


def php_prefix() -> Path:
    configured = subprocess.check_output(["php-config", "--prefix"], text=True).strip()
    return Path(configured).resolve()


def extension_output(prefix: Path, name: str) -> Path:
    return prefix / "lib" / "phishgate" / "php" / "extensions" / f"{name}.so"


def validate_php() -> None:
    version = subprocess.check_output(["php", "-r", "echo PHP_VERSION;"], text=True)
    if version.strip() != PHP_VERSION:
        raise SystemExit(f"PHP {PHP_VERSION} is required; found {version.strip()}.")
    if platform.system() != "Linux":
        raise SystemExit("The Conda PHP runtime is supported on Linux only.")


def extension_works(name: str, path: Path) -> bool:
    if not path.is_file():
        return False
    expression = "exit((" + " && ".join(
        f"function_exists('{function}')"
        for function in EXTENSIONS[name]["functions"]
    ) + ") ? 0 : 1);"
    result = subprocess.run(
        ["php", "-n", "-d", f"extension={path}", "-r", expression],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def safe_extract(archive: Path, destination: Path) -> None:
    destination_resolved = destination.resolve()
    with tarfile.open(archive, "r:gz") as source:
        for member in source.getmembers():
            member_path = (destination / member.name).resolve()
            if (
                member_path != destination_resolved
                and destination_resolved not in member_path.parents
            ):
                raise SystemExit(f"Unsafe path in PHP source archive: {member.name}")
        source.extractall(destination)


def find_compiler(prefix: Path) -> Path:
    candidates = sorted((prefix / "bin").glob("*-conda-linux-gnu-cc"))
    if not candidates:
        raise SystemExit("Conda C compiler is missing; rerun bash setup_environment.sh.")
    return candidates[0]


def build_extensions(prefix: Path, names: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="phishgate-php-") as temporary:
        work = Path(temporary)
        archive = work / f"php-{PHP_VERSION}.tar.gz"
        print(f"Downloading official PHP {PHP_VERSION} source...")
        urllib.request.urlretrieve(PHP_SOURCE_URL, archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != PHP_SOURCE_SHA256:
            raise SystemExit("PHP source checksum does not match the pinned release.")
        safe_extract(archive, work)

        build_env = os.environ.copy()
        build_env.update(
            {
                "CC": str(find_compiler(prefix)),
                "CPPFLAGS": f"-I{prefix / 'include'}",
                "LDFLAGS": f"-Wl,-rpath,{prefix / 'lib'} -L{prefix / 'lib'}",
                "PKG_CONFIG_PATH": os.pathsep.join(
                    (str(prefix / "lib" / "pkgconfig"), str(prefix / "share" / "pkgconfig"))
                ),
            }
        )
        for name in names:
            source = work / f"php-{PHP_VERSION}" / "ext" / name
            # Bundled-only extensions such as zlib name this file config0.m4.
            # phpize requires config.m4 to build the same code as a shared module.
            bundled_config = source / "config0.m4"
            shared_config = source / "config.m4"
            if bundled_config.is_file() and not shared_config.exists():
                shutil.copy2(bundled_config, shared_config)

            print(f"Building PHP ext/{name} for the Conda PHP ABI...")
            run(["phpize"], cwd=source, env=build_env)
            configure = str(EXTENSIONS[name]["configure"]).format(prefix=prefix)
            run(["./configure", configure], cwd=source, env=build_env)
            run(["make", "-j2"], cwd=source, env=build_env)

            output = extension_output(prefix, name)
            built = source / "modules" / f"{name}.so"
            output.parent.mkdir(parents=True, exist_ok=True)
            staged = output.with_suffix(".so.new")
            shutil.copy2(built, staged)
            os.replace(staged, output)


def main() -> None:
    validate_php()
    prefix = php_prefix()
    pending = [
        name
        for name in EXTENSIONS
        if not extension_works(name, extension_output(prefix, name))
    ]
    if pending:
        build_extensions(prefix, pending)

    for name in EXTENSIONS:
        output = extension_output(prefix, name)
        if not extension_works(name, output):
            raise SystemExit(f"Built PHP {name} extension failed its load check: {output}")
        print(f"Conda PHP {name} extension is ready: {output}")


if __name__ == "__main__":
    main()
