export const OMIT_VALUE = Symbol("omit-value");

export const RESERVED_FIELDS = [
  { key: "reserved1", label: "预留字段1", type: "text", defaultValue: "", hideInForm: true },
  { key: "reserved2", label: "预留字段2", type: "text", defaultValue: "", hideInForm: true },
  { key: "reserved3", label: "预留字段3", type: "text", defaultValue: "", hideInForm: true },
  { key: "reserved4", label: "预留字段4", type: "text", defaultValue: "", hideInForm: true },
  { key: "reserved5", label: "预留字段5", type: "text", defaultValue: "", hideInForm: true },
];

/** Keys always sent as empty strings on POST/PATCH; not shown in admin form. */
export const RESERVED_FIELD_KEYS = RESERVED_FIELDS.map((field) => field.key);
