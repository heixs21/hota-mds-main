/** Map admin API / form errors to short, user-facing Chinese messages. */

const DRF_PHRASES = [
  [/^\s*this field is required\.?\s*$/i, "为必填项。"],
  [/^\s*this field may not be (blank|null)\.?\s*$/i, "不能为空。"],
  [/^\s*not a valid string\.?\s*$/i, "须为有效文本。"],
  [/^\s*not a valid integer\.?\s*$/i, "须为整数。"],
  [/^\s*not a valid boolean\.?\s*$/i, "须选择是或否。"],
  [/^\s*a valid number is required\.?\s*$/i, "须为有效数字。"],
  [/^\s*enter a whole number\.?\s*$/i, "须为整数。"],
  [/^\s*ensure this field has no more than (\d+) characters\.?\s*$/i, "长度不能超过 $1 个字符。"],
  [/^\s*ensure this field has at least (\d+) characters\.?\s*$/i, "长度不能少于 $1 个字符。"],
  [/invalid pk "[^"]*" - object does not exist\.?/i, "关联记录不存在或已被删除。"],
  [/^\s*object with .* does not exist\.?\s*$/i, "关联记录不存在或已被删除。"],
  [/^\s*invalid hyperlink\.?\s*$/i, "关联对象无效。"],
  [/employee_no must contain only english letters and digits/i, "只能包含英文字母与数字。"],
  [/^\s*invalid username or password\.?\s*$/i, "账号或密码不正确。"],
  [/^\s*username and password are required\.?\s*$/i, "请输入账号和密码。"],
  [/^\s*invalid or missing admin token\.?\s*$/i, "登录已失效，请重新登录。"],
  [/^\s*admin permission required\.?\s*$/i, "没有后台访问权限。"],
  [/^\s*backend response is invalid\.?\s*$/i, "服务器返回了无法解析的数据，请稍后重试。"],
  [/^\s*request failed\.?\s*$/i, "请求失败，请稍后重试。"],
];

function applyPhraseTable(text) {
  const trimmed = typeof text === "string" ? text.trim() : "";
  if (!trimmed) {
    return "";
  }
  for (const [pattern, replacement] of DRF_PHRASES) {
    if (pattern.test(trimmed)) {
      return trimmed.replace(pattern, replacement);
    }
  }
  return trimmed;
}

function snakeCaseToCamelCase(key) {
  if (!key || typeof key !== "string") {
    return key;
  }
  if (!key.includes("_")) {
    return key;
  }
  return key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

function resolveFieldLabel(apiFieldKey, fields) {
  if (!apiFieldKey || !Array.isArray(fields)) {
    return null;
  }
  const direct = fields.find((f) => f.key === apiFieldKey);
  if (direct) {
    return direct.label;
  }
  const camel = snakeCaseToCamelCase(apiFieldKey);
  const byCamel = fields.find((f) => f.key === camel);
  return byCamel?.label ?? null;
}

function flattenValidationMessages(value, out, parentKey) {
  if (value === null || value === undefined) {
    return;
  }
  if (typeof value === "string") {
    out.push({ fieldKey: parentKey, message: value });
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      flattenValidationMessages(item, out, parentKey);
    }
    return;
  }
  if (typeof value === "object") {
    for (const [key, nested] of Object.entries(value)) {
      const nextKey = key === "detail" || key === "non_field_errors" ? parentKey : key;
      flattenValidationMessages(nested, out, nextKey ?? parentKey);
    }
  }
}

function translateDetailFragment(text) {
  return applyPhraseTable(text);
}

/**
 * Turn JSON.parse SyntaxError into a field-scoped hint (no raw engine positions).
 * @param {{ label: string }} field
 * @param {SyntaxError} syntaxError
 */
export function humanizeJsonFieldSyntaxError(field, syntaxError) {
  const label = field?.label ?? "该字段";
  const raw = typeof syntaxError?.message === "string" ? syntaxError.message : "";
  const lower = raw.toLowerCase();

  if (/expected property name|expected double-quoted property name/i.test(raw)) {
    return `「${label}」里属性名必须用英文双引号括起来，形如 "名称": 值，并注意逗号只能出现在属性与属性之间。`;
  }
  if (/unexpected token/i.test(lower)) {
    return `「${label}」中有无法识别的符号或标点，请检查是否多写了逗号、漏了引号或括号没有配对。`;
  }
  if (/unexpected end of json input/i.test(lower)) {
    return `「${label}」的 JSON 尚未写完或末尾缺少括号，请补全后再保存。`;
  }
  if (/bad escaped character/i.test(lower)) {
    return `「${label}」的 JSON 里反斜杠转义写法不正确，请检查 \\ 与引号。`;
  }
  if (/bad control character/i.test(lower)) {
    return `「${label}」的 JSON 中包含了不允许的控制字符，请删除异常换行或特殊字符。`;
  }
  if (/expected ',' or '\}'/i.test(raw) || /expected ',' or '\]'/i.test(raw)) {
    return `「${label}」的 JSON 在某一位置缺少逗号，或括号/方括号没有正确闭合。`;
  }
  return `「${label}」的内容不是合法的 JSON，请检查引号、逗号与大括号是否配对。`;
}

/**
 * Map fetch / unified API errors to a short Chinese message.
 * @param {Error & { status?: number, code?: string, data?: unknown }} error
 * @param {{ key: string, label: string }[]} fields
 * @param {{ fallback?: string }} [options]
 */
export function humanizeAdminApiError(error, fields, options = {}) {
  const fallback = options.fallback ?? "操作失败，请稍后重试。";
  const msg = typeof error?.message === "string" ? error.message.trim() : "";

  if (msg === "Failed to fetch" || /networkerror|load failed|failed to fetch/i.test(msg)) {
    return "无法连接服务器，请检查网络或接口地址（VITE_API_BASE_URL）是否正确。";
  }

  const status = error?.status;
  if (status === 403) {
    return "没有权限执行此操作。";
  }
  if (status === 404) {
    return "未找到相关记录，可能已被删除。";
  }
  if (typeof status === "number" && status >= 500) {
    return "服务器暂时不可用，请稍后再试。";
  }

  const data = error?.data;
  const rows = [];
  if (data && typeof data === "object" && !Array.isArray(data)) {
    flattenValidationMessages(data, rows, null);
  }

  const labeled = rows
    .map(({ fieldKey, message }) => {
      const piece = translateDetailFragment(message);
      if (!piece) {
        return null;
      }
      const label = fieldKey ? resolveFieldLabel(fieldKey, fields) : null;
      if (label) {
        return `「${label}」${piece}`;
      }
      return piece;
    })
    .filter(Boolean);

  if (labeled.length > 0) {
    const unique = [...new Set(labeled)];
    return unique.slice(0, 3).join(" ");
  }

  const friendly = translateDetailFragment(msg);
  if (friendly && friendly !== msg) {
    return friendly;
  }
  if (/json at position/i.test(msg)) {
    return fallback;
  }
  if (msg && !/[{}[\]]/.test(msg) && msg.length < 120) {
    return msg;
  }
  return fallback;
}
