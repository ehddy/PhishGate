#!/bin/sh

set -eu

: "${PHISHDECLOAKER_DOCROOT:?Set PHISHDECLOAKER_DOCROOT to the extracted PhishDecloaker directory}"
PHISHDECLOAKER_LISTEN_HOST="${PHISHDECLOAKER_LISTEN_HOST:-127.0.0.1}"
PHISHDECLOAKER_LISTEN_PORT="${PHISHDECLOAKER_LISTEN_PORT:-8081}"
PHISHDECLOAKER_PHP_BIN="${PHISHDECLOAKER_PHP_BIN:-php}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PHP_SAFETY_INI="${PHISHGATE_PHP_SAFETY_INI:-${SCRIPT_DIR}/phishgate-safety.ini}"
PHP_ROUTER="${PHISHGATE_PHP_ROUTER:-${SCRIPT_DIR}/router.php}"

# Preserve local rendering, PHP sessions, and ordinary local file helpers while
# preventing kit-controlled delivery, outbound sockets, command execution, and
# uploads. allow_url_fopen=0 separately blocks URL wrappers used by functions
# such as file_get_contents(). The dataset must contain synthetic inputs only.
if [ ! -r "${PHP_SAFETY_INI}" ]; then
    echo "PhishGate PHP safety configuration is not readable: ${PHP_SAFETY_INI}" >&2
    exit 1
fi

if [ ! -r "${PHP_ROUTER}" ]; then
    echo "PhishGate PHP router is not readable: ${PHP_ROUTER}" >&2
    exit 1
fi

DISABLED_FUNCTIONS="$(sed -n 's/^[[:space:]]*disable_functions[[:space:]]*=[[:space:]]*//p' "${PHP_SAFETY_INI}")"
SENDMAIL_PATH="$(sed -n 's/^[[:space:]]*sendmail_path[[:space:]]*=[[:space:]]*//p' "${PHP_SAFETY_INI}")"

if [ -z "${DISABLED_FUNCTIONS}" ] || [ -z "${SENDMAIL_PATH}" ]; then
    echo "PhishGate PHP safety configuration is missing required values." >&2
    exit 1
fi

set -- "${PHISHDECLOAKER_PHP_BIN}"
if [ -n "${PHISHGATE_PHP_CURL_EXTENSION:-}" ]; then
    if [ ! -r "${PHISHGATE_PHP_CURL_EXTENSION}" ]; then
        echo "PhishGate PHP curl extension is not readable: ${PHISHGATE_PHP_CURL_EXTENSION}" >&2
        exit 1
    fi
    set -- "$@" -d "extension=${PHISHGATE_PHP_CURL_EXTENSION}"
fi
if [ -n "${PHISHGATE_PHP_ZLIB_EXTENSION:-}" ]; then
    if [ ! -r "${PHISHGATE_PHP_ZLIB_EXTENSION}" ]; then
        echo "PhishGate PHP zlib extension is not readable: ${PHISHGATE_PHP_ZLIB_EXTENSION}" >&2
        exit 1
    fi
    set -- "$@" -d "extension=${PHISHGATE_PHP_ZLIB_EXTENSION}"
fi

exec "$@" \
    -d "disable_functions=${DISABLED_FUNCTIONS}" \
    -d "sendmail_path=${SENDMAIL_PATH}" \
    -d allow_url_fopen=0 \
    -d allow_url_include=0 \
    -d log_errors=0 \
    -d display_errors=0 \
    -d display_startup_errors=0 \
    -d max_execution_time=20 \
    -S "${PHISHDECLOAKER_LISTEN_HOST}:${PHISHDECLOAKER_LISTEN_PORT}" \
    -t "${PHISHDECLOAKER_DOCROOT}" \
    "${PHP_ROUTER}"
