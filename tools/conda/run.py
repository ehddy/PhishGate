#!/usr/bin/env python3
"""Run the complete PhishGate stack without Docker.

The process tree is intentionally local-only: FastAPI owns gates, proxying,
and (with a pre-built frontend/dist/, see FRONTEND_DIST) the public SPA
itself; separate PHP servers expose the extracted PhishDecloaker and
selected DynaPD directories only to FastAPI. Without a pre-built dist/,
Vite's dev server is the public entry point instead, proxying anything
that isn't its own asset to FastAPI on loopback.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"
PHISHDECLOAKER_ROOT = (
    ROOT / "data" / "private" / "phishdecloaker" / "extracted" / "src"
)
DYNAPD_ROOT = ROOT / "data" / "private" / "dynapd" / "raw_selected"
DYNAPD_SELECTION = ROOT / "data" / "private" / "dynapd" / "selection.csv"
# A pre-built frontend/dist/ (see README, "Conda" -- rsync/scp it in like
# any other private artifact, never commit it) lets
# FastAPI serve the SPA itself, the same way Nginx does for Docker's `prod`
# profile. When absent, the launcher falls back to running Vite's dev server
# as its own process, which needs the separate PhishGate-node Conda
# environment because PHP 7.4 and Node 22 require incompatible OpenSSL ranges.
FRONTEND_DIST = ROOT / "frontend" / "dist"
BACKEND_PORT = "8000"
PHISHDECLOAKER_PORT = "8081"
DYNAPD_PORT = "8082"
# PHP serves a disposable copy of the extracted kits so kit-side writes (visit
# logs, submitted-value files, kit4's per-visit a1b2c3/<md5>/ copies) never
# reach the dataset. The location is fixed, and wiped on both start and exit,
# so an interrupted run leaves at most one stale copy behind.
RUNTIME_ROOT = ROOT / "tmp" / "conda-runtime"
PHISHDECLOAKER_RUNTIME_ROOT = RUNTIME_ROOT / "phishdecloaker"
PHISHDECLOAKER_LAUNCHER = ROOT / "tools" / "runtime" / "start_phishdecloaker_php.sh"
DYNAPD_LAUNCHER = ROOT / "tools" / "runtime" / "start_dynapd_php.sh"


def frontend_build_ready() -> bool:
    """Return whether dist contains an index and at least one built asset."""
    assets = FRONTEND_DIST / "assets"
    return (
        (FRONTEND_DIST / "index.html").is_file()
        and assets.is_dir()
        and any(path.is_file() for path in assets.rglob("*"))
    )


def php_extension_paths() -> dict[str, Path]:
    """Return setup-managed extension paths for the active Conda PHP."""
    try:
        prefix = subprocess.check_output(
            ["php-config", "--prefix"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise SystemExit("Missing php-config. Run bash setup_environment.sh first.") from None
    directory = Path(prefix) / "lib" / "phishgate" / "php" / "extensions"
    return {name: directory / f"{name}.so" for name in ("curl", "zlib")}


def require_php_extensions() -> dict[str, Path]:
    extensions = php_extension_paths()
    check = subprocess.run(
        [
            "php",
            "-n",
            "-d",
            f"extension={extensions['curl']}",
            "-d",
            f"extension={extensions['zlib']}",
            "-r",
            "exit(function_exists('curl_version') && function_exists('curl_init') "
            "&& function_exists('gzinflate') ? 0 : 1);",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if check.returncode != 0:
        raise SystemExit(
            "The Conda PHP 7.4 curl/zlib extensions are missing or incompatible. "
            "Run bash setup_environment.sh first."
        )
    return extensions


def read_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        raise SystemExit(f"{ENV_PATH} not found. Copy .env.example to .env first.")

    values: dict[str, str] = {}
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def generic_mode(file_env: dict[str, str] | None = None) -> bool:
    """Whether the generic gate-injection mode is on (no bundled datasets)."""
    env = {**os.environ, **(file_env or {})}
    return bool(env.get("PHISHGATE_GENERIC_UPSTREAM", "").strip())


def require_runtime() -> None:
    generic = generic_mode(read_env())
    # A pre-built frontend/dist/ makes FastAPI the public entry point, so
    # Node (and the separate PhishGate-node environment) is only required
    # when there is no dist/ to serve and Vite's dev server must run instead.
    serve_prebuilt = frontend_build_ready()
    if FRONTEND_DIST.exists() and not serve_prebuilt:
        raise SystemExit(
            f"Incomplete frontend build at {FRONTEND_DIST}. Rebuild it or remove "
            "the directory to use the Vite development server."
        )
    # Generic mode gates one operator-configured upstream and runs no local PHP
    # kit servers, so PHP, the compiled extensions, and the datasets are not
    # required -- only the frontend (Vite or a pre-built dist) and FastAPI.
    base_commands = () if generic else ("php",)
    required_commands = base_commands if serve_prebuilt else ("node", "npm") + base_commands
    missing = [name for name in required_commands if shutil.which(name) is None]
    if missing:
        raise SystemExit(
            f"Missing Conda runtime command(s): {', '.join(missing)}. "
            "Activate the Conda environment(s) first: `conda activate PhishGate`"
            + ("" if serve_prebuilt else " && conda activate --stack PhishGate-node")
            + "."
        )
    if not generic:
        require_php_extensions()
        if not (PHISHDECLOAKER_ROOT / "kit1").is_dir():
            raise SystemExit(
                "PhishDecloaker data is missing. Extract the official archive so "
                f"{PHISHDECLOAKER_ROOT / 'kit1'} exists."
            )
        if not DYNAPD_SELECTION.is_file() or not DYNAPD_ROOT.is_dir():
            raise SystemExit(
                "DynaPD staging is missing. Generate selection.csv and raw_selected/ "
                "with scripts/dataset/import_dynapd_selection.py first."
            )
        for label, launcher in (
            ("PhishDecloaker", PHISHDECLOAKER_LAUNCHER),
            ("DynaPD", DYNAPD_LAUNCHER),
        ):
            if not launcher.is_file():
                raise SystemExit(f"{label} PHP launcher is missing: {launcher}")
    elif not os.environ.get("PHISHGATE_UPSTREAM", "").strip() and not read_env().get("PHISHGATE_UPSTREAM", "").strip():
        raise SystemExit(
            "Generic mode needs PHISHGATE_UPSTREAM set to the upstream to gate "
            "(and its host in PHISHGATE_UPSTREAM_ALLOWED_HOSTS)."
        )
    if not serve_prebuilt and not (ROOT / "frontend" / "node_modules").is_dir():
        raise SystemExit("Frontend dependencies are missing. Run bash setup_environment.sh first.")


def remove_phishdecloaker_runtime_copy() -> None:
    target = PHISHDECLOAKER_RUNTIME_ROOT
    # Guard the recursive delete: it must stay inside tmp/ and never overlap
    # the extracted dataset, even if tmp/ is later replaced by a symlink.
    resolved = target.resolve()
    dataset = PHISHDECLOAKER_ROOT.resolve()
    if (
        (ROOT / "tmp").resolve() not in resolved.parents
        or resolved == dataset
        or dataset in resolved.parents
        or resolved in dataset.parents
    ):
        raise SystemExit(f"Refusing to remove unexpected runtime path: {target}")
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)


def prepare_phishdecloaker_runtime_copy() -> Path:
    remove_phishdecloaker_runtime_copy()
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    print("Copying PhishDecloaker kits into a disposable runtime directory...")
    # copytree keeps file and directory modes, e.g. the exact 0777 that
    # kit4's php_check.php requires on a1b2c3/ and iplogs/.
    shutil.copytree(PHISHDECLOAKER_ROOT, PHISHDECLOAKER_RUNTIME_ROOT, symlinks=True)
    return PHISHDECLOAKER_RUNTIME_ROOT


def runtime_env(file_env: dict[str, str]) -> dict[str, str]:
    env = {**os.environ, **file_env}
    generic = generic_mode(file_env)
    required = ("PHISHGATE_SEED", "PHISHGATE_PROFILE")
    missing = [name for name in required if not env.get(name, "").strip()]
    if missing:
        raise SystemExit(
            f"Missing .env value(s): {', '.join(missing)}. "
            "Set them before starting the runtime."
        )
    if env["PHISHGATE_SEED"].strip() == "change-me-per-experiment":
        raise SystemExit(
            "PHISHGATE_SEED still uses the example placeholder. "
            "Set a private experiment seed before starting the runtime."
        )

    logs_dir = ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    common = {
        "PYTHONPATH": str(ROOT / "backend"),
        "PHISHGATE_CONFIG": str(ROOT / "config" / "profiles.yaml"),
        "PHISHGATE_LOG_DIR": str(logs_dir),
        "VITE_PHISHGATE_BACKEND_URL": f"http://127.0.0.1:{BACKEND_PORT}",
        "PHISHGATE_FRONTEND_DIST": str(FRONTEND_DIST),
    }
    if generic:
        # Keep the operator's PHISHGATE_UPSTREAM (and allowlist) from .env; run
        # no local PHP kit servers and mount no datasets.
        env.update(common)
    else:
        php_extensions = require_php_extensions()
        env.update(
            {
                **common,
                "PHISHGATE_UPSTREAM": f"http://127.0.0.1:{PHISHDECLOAKER_PORT}",
                "PHISHGATE_DYNAPD_UPSTREAM": f"http://127.0.0.1:{DYNAPD_PORT}",
                "PHISHDECLOAKER_DOCROOT": str(PHISHDECLOAKER_RUNTIME_ROOT),
                "PHISHDECLOAKER_LISTEN_HOST": "127.0.0.1",
                "PHISHDECLOAKER_LISTEN_PORT": PHISHDECLOAKER_PORT,
                "PHISHGATE_DYNAPD_SELECTION": str(DYNAPD_SELECTION),
                "DYNAPD_DOCROOT": str(DYNAPD_ROOT),
                "DYNAPD_LISTEN_HOST": "127.0.0.1",
                "DYNAPD_LISTEN_PORT": DYNAPD_PORT,
                "PHISHGATE_BRAND_ANNOTATION": str(ROOT / "data" / "kit_brand_annotation.csv"),
                "PHISHGATE_MANUAL_ANNOTATION": str(ROOT / "data" / "manual_annotation.csv"),
                "PHISHGATE_MANUAL_BENIGN_ANNOTATION": str(
                    ROOT / "data" / "manual_benign_annotation.csv"
                ),
                "PHISHGATE_MANUAL_SAMPLES": str(ROOT / "data" / "manual" / "samples"),
                "PHISHGATE_PHP_CURL_EXTENSION": str(php_extensions["curl"]),
                "PHISHGATE_PHP_ZLIB_EXTENSION": str(php_extensions["zlib"]),
            }
        )

    manifest = os.environ.get(
        "PHISHGATE_EXPERIMENT_MANIFEST",
        env.get("PHISHGATE_EXPERIMENT_MANIFEST", ""),
    ).strip()
    if manifest.startswith("/app/config/"):
        env["PHISHGATE_EXPERIMENT_MANIFEST"] = str(ROOT / "config" / Path(manifest).name)
    elif manifest.startswith("/app/targets/"):
        relative = Path(manifest).relative_to("/app/targets")
        env["PHISHGATE_EXPERIMENT_MANIFEST"] = str(ROOT / "targets" / relative)
    return env


def start_processes(env: dict[str, str]) -> list[tuple[str, subprocess.Popen[bytes]]]:
    public_host = env.get("PHISHGATE_HOST", "127.0.0.1").strip() or "127.0.0.1"
    public_port = env.get("PHISHGATE_PORT", "8080").strip() or "8080"
    # With a pre-built frontend/dist/, FastAPI serves the SPA itself (see
    # backend/app/main.py), so it becomes the public entry point directly and
    # no separate Vite process is needed -- mirroring Docker's `prod` profile,
    # where Nginx, not Vite, is what's public. Without dist/, Vite remains the
    # public entry point and proxies everything else to backend on loopback,
    # exactly as before.
    serve_prebuilt = frontend_build_ready()
    backend_host = public_host if serve_prebuilt else "127.0.0.1"
    backend_port = public_port if serve_prebuilt else BACKEND_PORT
    # Generic mode gates the operator's own upstream, so no local PHP kit
    # servers run.
    commands = [] if generic_mode(env) else [
        (
            "phishdecloaker-php",
            ("sh", str(PHISHDECLOAKER_LAUNCHER)),
            ROOT,
            False,
        ),
        (
            "dynapd-php",
            ("sh", str(DYNAPD_LAUNCHER)),
            ROOT,
            True,
        ),
    ]
    commands += [
        (
            "backend",
            (
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                backend_host,
                "--port",
                backend_port,
            ),
            ROOT / "backend",
            False,
        ),
    ]
    if not serve_prebuilt:
        commands.append(
            (
                "frontend",
                ("npm", "run", "serve", "--", "--host", public_host, "--port", public_port),
                ROOT / "frontend",
                False,
            )
        )
    processes: list[tuple[str, subprocess.Popen[bytes]]] = []
    try:
        for name, command, cwd, quiet in commands:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                start_new_session=True,
                stdin=subprocess.DEVNULL if quiet else None,
                stdout=subprocess.DEVNULL if quiet else None,
                stderr=subprocess.DEVNULL if quiet else None,
            )
            processes.append((name, process))
    except Exception:
        stop_processes(processes)
        raise
    return processes


def stop_processes(processes: list[tuple[str, subprocess.Popen[bytes]]]) -> None:
    for _, process in processes:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
    deadline = time.monotonic() + 5
    for _, process in processes:
        if process.poll() is not None:
            continue
        try:
            process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)


def raise_keyboard_interrupt(signum: int, frame: object) -> None:
    raise KeyboardInterrupt


UNPRIVILEGED_PORT_START = Path("/proc/sys/net/ipv4/ip_unprivileged_port_start")


def unprivileged_port_start() -> int:
    """Lowest port a non-root process may bind (Linux sysctl, default 1024)."""
    try:
        return int(UNPRIVILEGED_PORT_START.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 1024


def require_bindable_public_port(port: str) -> None:
    """Fail before copying kits when Vite could never bind the public port."""
    if not port.isdigit() or os.geteuid() == 0:
        return
    lowest = unprivileged_port_start()
    if int(port) < lowest:
        raise SystemExit(
            f"PHISHGATE_PORT={port} is below this system's unprivileged port "
            f"start ({lowest}), so Vite cannot open it without root. Either run "
            f"`sudo sysctl -w net.ipv4.ip_unprivileged_port_start={port}` once "
            "(see README), or set PHISHGATE_PORT=8080 in .env and re-run "
            "python3 scripts/prepare_experiment.py."
        )


def install_shutdown_signals() -> None:
    """Route SIGTERM/SIGHUP through the finally block that removes the copy.

    A closed SSH session (SIGHUP) or `kill` (SIGTERM) must still clean up. A
    launcher that already ignores SIGHUP (`nohup`) asked to survive logout,
    so that choice is kept.
    """
    signal.signal(signal.SIGTERM, raise_keyboard_interrupt)
    if signal.getsignal(signal.SIGHUP) is not signal.SIG_IGN:
        signal.signal(signal.SIGHUP, raise_keyboard_interrupt)


def main() -> None:
    require_runtime()
    env = runtime_env(read_env())
    public_host = env.get("PHISHGATE_HOST", "127.0.0.1")
    public_port = env.get("PHISHGATE_PORT", "8080")
    require_bindable_public_port(public_port.strip() or "8080")

    install_shutdown_signals()

    processes: list[tuple[str, subprocess.Popen[bytes]]] = []
    try:
        if not generic_mode(env):
            prepare_phishdecloaker_runtime_copy()
        processes = start_processes(env)
        print(f"PhishGate is starting at http://{public_host}:{public_port}/")
        running = ", ".join(name for name, _ in processes)
        print(f"Press Ctrl-C to stop all of: {running}.")
        while True:
            for name, process in processes:
                return_code = process.poll()
                if return_code is not None:
                    raise RuntimeError(f"{name} exited unexpectedly with status {return_code}.")
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\nStopping PhishGate...")
    finally:
        stop_processes(processes)
        remove_phishdecloaker_runtime_copy()


if __name__ == "__main__":
    main()
