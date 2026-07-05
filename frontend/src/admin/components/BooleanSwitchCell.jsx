import { Switch } from "antd";

export function BooleanSwitchCell({ checked, disabled, loading, onChange }) {
  return (
    <Switch
      checked={Boolean(checked)}
      disabled={disabled}
      loading={loading}
      onChange={onChange}
      size="small"
    />
  );
}
