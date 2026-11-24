#!/usr/bin/env bash

set -euo pipefail

ENV_NAME="PhishGate"
NODE_ENV_NAME="PhishGate-node"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PROJECT_ROOT}/environment.yml"
NODE_ENV_FILE="${PROJECT_ROOT}/tools/conda/environment-node.yml"
FRONTEND_DIST="${PHISHGATE_FRONTEND_DIST:-${PROJECT_ROOT}/frontend/dist}"
FRONTEND_INDEX="${FRONTEND_DIST}/index.html"
FRONTEND_ASSETS="${FRONTEND_DIST}/assets"

cd "${PROJECT_ROOT}"

if ! command -v conda >/dev/null 2>&1; then
    echo "Error: conda is not available on PATH." >&2
    exit 1
fi

update_environment() {
    local name="$1"
    local file="$2"
    if conda run -n "${name}" true >/dev/null 2>&1; then
        echo "Updating the existing ${name} Conda environment..."
        # Remove packages that belonged to an older environment definition.
        # In particular, nodejs must leave the runtime environment before
        # php=7.4 can replace PHP 8/OpenSSL 3 without an unsatisfiable solve.
        conda env update --prune -n "${name}" -f "${file}"
    else
        echo "Creating the ${name} Conda environment..."
        conda env create -f "${file}"
    fi
}

update_environment "${ENV_NAME}" "${ENV_FILE}"

echo "Building PHP 7.4 extensions omitted by the Conda package..."
conda run --no-capture-output -n "${ENV_NAME}" \
    python tools/conda/build_php_extensions.py

# nodejs=22 lives in its own environment: conda-forge's nodejs=22 needs
# openssl>=3.3, while php=7.4 needs openssl<1.1.2. A runtime server with a
# transferred production build does not need Node at all. Auto mode installs
# it only when dist/index.html is absent; builders can force either choice.
case "${PHISHGATE_SETUP_NODE:-auto}" in
    auto)
        if [[ -f "${FRONTEND_INDEX}" && -d "${FRONTEND_ASSETS}" ]] \
            && find "${FRONTEND_ASSETS}" -type f -print -quit | grep -q .; then
            SETUP_NODE=false
        else
            SETUP_NODE=true
        fi
        ;;
    1|true|yes)
        SETUP_NODE=true
        ;;
    0|false|no)
        SETUP_NODE=false
        ;;
    *)
        echo "Error: PHISHGATE_SETUP_NODE must be auto, 1, or 0." >&2
        exit 1
        ;;
esac

if [[ "${SETUP_NODE}" == false ]] \
    && { [[ ! -f "${FRONTEND_INDEX}" || ! -d "${FRONTEND_ASSETS}" ]] \
        || ! find "${FRONTEND_ASSETS}" -type f -print -quit | grep -q .; }; then
    echo "Error: Node setup can be skipped only when ${FRONTEND_DIST} contains index.html and built assets." >&2
    exit 1
fi

if [[ "${SETUP_NODE}" == true ]]; then
    update_environment "${NODE_ENV_NAME}" "${NODE_ENV_FILE}"
    echo "Installing the Vue development dependencies..."
    conda run --no-capture-output -n "${NODE_ENV_NAME}" npm --prefix frontend install \
        --no-audit --no-fund
else
    echo "Using pre-built frontend/dist; skipping the Node environment."
fi

echo "Checking the runtime dependencies..."
conda run --no-capture-output -n "${ENV_NAME}" python -m pip check
conda run --no-capture-output -n "${ENV_NAME}" python -c \
    "import bs4, fastapi, PIL, uvicorn, yaml; print('Python imports passed.')"
conda run --no-capture-output -n "${ENV_NAME}" php --version
if [[ "${SETUP_NODE}" == true ]]; then
    conda run --no-capture-output -n "${NODE_ENV_NAME}" node --version
fi

echo
echo "Environment setup completed successfully."
if [[ "${SETUP_NODE}" == true ]]; then
    echo "Activate both with: conda activate ${ENV_NAME} && conda activate --stack ${NODE_ENV_NAME}"
else
    echo "Activate it with: conda activate ${ENV_NAME}"
fi
