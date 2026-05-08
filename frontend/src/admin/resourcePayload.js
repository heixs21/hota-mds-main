import { OMIT_VALUE, parseFieldValue } from "../adminResources.js";

export function buildPayloadFromForm(resourceDefinition, formState) {
  const payload = {};
  const nestedBuckets = {};

  for (const field of resourceDefinition.fields) {
    let parsedValue;
    try {
      parsedValue = parseFieldValue(field, formState[field.key], formState);
    } catch (parseErr) {
      if (parseErr instanceof SyntaxError && (field.type === "json" || field.type === "screenPageTransfer")) {
        throw { kind: "json", field, error: parseErr };
      }
      throw parseErr;
    }
    if (field.type === "integer" && parsedValue !== null && Number.isNaN(parsedValue)) {
      throw { kind: "integer", field };
    }
    if (parsedValue === OMIT_VALUE) {
      continue;
    }

    if (field.storage) {
      if (!nestedBuckets[field.storage]) {
        nestedBuckets[field.storage] = {};
      }
      if (parsedValue !== null && parsedValue !== "") {
        nestedBuckets[field.storage][field.key] = parsedValue;
      }
    } else {
      payload[field.key] = parsedValue;
    }
  }

  for (const [storageKey, bucket] of Object.entries(nestedBuckets)) {
    payload[storageKey] = bucket;
  }

  if (resourceDefinition.fixedSourceType) {
    payload.sourceType = resourceDefinition.fixedSourceType;
  }

  return payload;
}
