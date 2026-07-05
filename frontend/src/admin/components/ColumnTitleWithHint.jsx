import { QuestionCircleOutlined } from "@ant-design/icons";
import { Tooltip } from "antd";

export function ColumnTitleWithHint({ hint, label }) {
  if (!hint) {
    return label;
  }

  return (
    <span className="resource-column-title">
      {label}
      <Tooltip title={hint}>
        <span aria-label={`${label}说明`} className="resource-column-title-hint" role="img">
          <QuestionCircleOutlined />
        </span>
      </Tooltip>
    </span>
  );
}
