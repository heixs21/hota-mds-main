import { DEFAULT_ADMIN_RESOURCE, resourceDefinitions } from "../adminResources.js";
import { ACTIVE_RESOURCE_STORAGE_PREFIX } from "./adminConstants.js";

export function buildActiveResourceStorageKey(username) {
  return `${ACTIVE_RESOURCE_STORAGE_PREFIX}:${username || "anonymous"}`;
}

export function pickValidResource(resourceKey) {
  return resourceDefinitions[resourceKey] ? resourceKey : DEFAULT_ADMIN_RESOURCE;
}

export function httpErrorToastVariant(status) {
  if (status === 403 || status === 404) {
    return "warning";
  }
  return "error";
}
