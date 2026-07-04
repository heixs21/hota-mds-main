import { LogoutOutlined, UserOutlined } from "@ant-design/icons";
import { Button, Dropdown, Layout, Space, Spin, Typography } from "antd";
import { Suspense, useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { DEFAULT_ADMIN_RESOURCE } from "../../adminResources.js";
import { useAdminSession } from "../context/AdminSessionContext.jsx";
import { buildActiveResourceStorageKey } from "../adminUtils.js";
import { pathToResourceKey } from "../routes/resourcePaths.js";
import AdminSidebar from "./AdminSidebar.jsx";

const { Content, Header } = Layout;

export default function AdminLayout() {
  const { currentUser, onLogout } = useAdminSession();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const activeResource = pathToResourceKey(location.pathname) ?? DEFAULT_ADMIN_RESOURCE;

  useEffect(() => {
    if (!currentUser?.username) {
      return;
    }
    window.localStorage.setItem(
      buildActiveResourceStorageKey(currentUser.username),
      activeResource,
    );
  }, [activeResource, currentUser?.username]);

  const userMenuItems = [
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "退出登录",
      onClick: onLogout,
    },
  ];

  return (
    <Layout className="admin-app">
      <Header className="admin-app-header">
        <Space direction="vertical" size={0}>
          <Typography.Title level={5} style={{ margin: 0 }}>
            后台管理控制台
          </Typography.Title>
          <Typography.Text type="secondary">HOTA MDS</Typography.Text>
        </Space>
        <Space align="center" size="middle">
          <Typography.Text type="secondary">{currentUser.displayName}</Typography.Text>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" trigger={["click"]}>
            <Button icon={<UserOutlined />} type="default">
              {currentUser.username}
            </Button>
          </Dropdown>
        </Space>
      </Header>

      <Layout className="admin-app-body">
        <Layout.Sider
          className="admin-app-sider"
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          width={220}
        >
          <AdminSidebar activeResource={activeResource} />
        </Layout.Sider>
        <Content className="admin-app-content">
          <Suspense
            fallback={
              <div className="admin-page-loading">
                <Spin size="large" />
              </div>
            }
          >
            <Outlet />
          </Suspense>
        </Content>
      </Layout>
    </Layout>
  );
}
