<?php

// PHP's built-in server serves a directory index without first adding the
// trailing slash that Apache's mod_dir would add. Relative redirects inside
// legacy kits then resolve against the parent directory. Canonicalize only
// real directories inside the configured document root before PHP executes.
$requestUri = $_SERVER['REQUEST_URI'] ?? '/';
$requestPath = parse_url($requestUri, PHP_URL_PATH);

if (is_string($requestPath) && $requestPath !== '/' && substr($requestPath, -1) !== '/') {
    $documentRoot = realpath($_SERVER['DOCUMENT_ROOT'] ?? '');
    $decodedPath = rawurldecode($requestPath);
    $candidate = $documentRoot === false
        ? false
        : realpath($documentRoot . DIRECTORY_SEPARATOR . ltrim($decodedPath, '/'));
    $insideDocumentRoot = $documentRoot !== false
        && $candidate !== false
        && strpos($candidate, $documentRoot . DIRECTORY_SEPARATOR) === 0;

    if ($insideDocumentRoot && is_dir($candidate)) {
        $query = parse_url($requestUri, PHP_URL_QUERY);
        $canonicalPath = '/' . ltrim($requestPath, '/');
        $location = $canonicalPath . '/' . (is_string($query) && $query !== '' ? '?' . $query : '');
        header('Location: ' . $location, true, 308);
        exit;
    }
}

return false;
