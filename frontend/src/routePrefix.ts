const prefix = window.location.pathname.split("/").filter(Boolean)[0] || "";

export const ROUTE_PREFIX = prefix ? `/${prefix}` : "";
