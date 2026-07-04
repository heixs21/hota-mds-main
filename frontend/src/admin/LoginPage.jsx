import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { Button, Card, Flex, Form, Input, Space, Typography } from "antd";

import hotaLogo from "../assets/hota-logo.png";

function LoginBrandHeader() {
  return (
    <Space align="center" className="login-brand" direction="vertical" size={8}>
      <img alt="和泰智造" className="login-brand-logo" height={72} src={hotaLogo} />
      <Typography.Title level={4} style={{ margin: 0 }}>
        和泰智造数屏系统
      </Typography.Title>
      <Typography.Text type="secondary">HOTA MDS · 后台管理</Typography.Text>
    </Space>
  );
}

export default function LoginPage({ isSubmitting, onSubmit }) {
  return (
    <Flex align="center" className="login-page" justify="center">
      <Card className="login-card">
        <LoginBrandHeader />

        <Typography.Paragraph className="login-card-intro" type="secondary">
          请使用管理员账号登录
        </Typography.Paragraph>

        <Form layout="vertical" onFinish={onSubmit} requiredMark={false}>
          <Form.Item
            label="管理员账号"
            name="username"
            rules={[{ required: true, message: "请输入管理员账号" }]}
          >
            <Input autoComplete="username" autoFocus placeholder="请输入管理员账号" prefix={<UserOutlined />} />
          </Form.Item>

          <Form.Item label="密码" name="password" rules={[{ required: true, message: "请输入密码" }]}>
            <Input.Password
              autoComplete="current-password"
              placeholder="请输入密码"
              prefix={<LockOutlined />}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button block htmlType="submit" loading={isSubmitting} type="primary">
              登 录
            </Button>
          </Form.Item>
        </Form>

        <Typography.Text className="login-card-footer" type="secondary">
          和泰智造 · HOTA MDS v2.0 · 仅限授权人员访问
        </Typography.Text>
      </Card>
    </Flex>
  );
}
