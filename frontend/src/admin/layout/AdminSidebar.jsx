import { MoonOutlined, SunOutlined } from "@ant-design/icons";
import { Button, Menu } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { buildAdminMenuItems, getAdminMenuOpenKeys } from "./adminMenu.js";
import { resourceKeyToPath } from "../routes/resourcePaths.js";

export default function AdminSidebar({ activeResource, theme, onToggleTheme }) {
  const navigate = useNavigate();
  const menuItems = useMemo(() => buildAdminMenuItems(), []);
  const selectedKeys = useMemo(() => [resourceKeyToPath(activeResource)], [activeResource]);
  const [openKeys, setOpenKeys] = useState(() => getAdminMenuOpenKeys(activeResource));

  useEffect(() => {
    setOpenKeys((previous) => {
      const required = getAdminMenuOpenKeys(activeResource);
      if (required.length === 0) {
        return previous;
      }
      return Array.from(new Set([...previous, ...required]));
    });
  }, [activeResource]);

  return (
    <div className="admin-sidebar">
      <Menu
        items={menuItems}
        mode="inline"
        openKeys={openKeys}
        selectedKeys={selectedKeys}
        style={{ borderInlineEnd: "none", flex: 1, overflow: "auto" }}
        theme={theme === "dark" ? "dark" : "light"}
        onClick={({ key }) => {
          if (key.startsWith("/admin/")) {
            navigate(key);
          }
        }}
        onOpenChange={setOpenKeys}
      />
      <div className="admin-sidebar-footer">
        <Button
          block
          icon={theme === "dark" ? <SunOutlined /> : <MoonOutlined />}
          onClick={onToggleTheme}
          type="text"
        >
          {theme === "dark" ? "切换明亮主题" : "切换暗色主题"}
        </Button>
      </div>
    </div>
  );
}
