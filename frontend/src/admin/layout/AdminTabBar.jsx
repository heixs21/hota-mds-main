import { Tabs } from "antd";

import { renderAdminMenuIcon } from "./adminMenuIcons.jsx";

/** 类面包屑：editable-card 标签栏，仅作导航；页面内容由 Outlet 渲染。 */
export default function AdminTabBar({ activeKey, onTabChange, onTabEdit, tabItems }) {
  if (tabItems.length === 0) {
    return null;
  }

  return (
    <div className="admin-tab-nav-wrap">
      <Tabs
        activeKey={activeKey}
        className="admin-tab-nav"
        hideAdd
        items={tabItems.map((tab) => ({
          key: tab.key,
          closable: tab.closable,
          label: (
            <span className="admin-tab-nav-label">
              {renderAdminMenuIcon(tab.resourceKey)}
              <span>{tab.label}</span>
            </span>
          ),
        }))}
        onChange={onTabChange}
        onEdit={onTabEdit}
        size="small"
        type="editable-card"
      />
    </div>
  );
}
