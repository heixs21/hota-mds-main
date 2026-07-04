import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Input, Typography } from "antd";

export default function LoginPage({
  errorMessage,
  isSubmitting,
  onSubmit,
  password,
  setPassword,
  setUsername,
  username,
}) {
  return (
    <main className="login-page">
      <div className="login-bg-pattern" aria-hidden="true" />
      <div className="login-container">
        <div className="login-brand">
          <div className="brand-icon">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <rect width="48" height="48" rx="12" fill="#5e6ad2" />
              <path d="M14 16h8v4h4v-4h8v16h-8v-4h-4v4h-8V16z" fill="#fff" fillOpacity="0.9" />
              <path d="M18 24h12v2H18v-2z" fill="#5e6ad2" />
            </svg>
          </div>
          <h1 className="brand-title">和泰智造数屏系统</h1>
          <p className="brand-subtitle">HOTA Manufacturing Digital Screen</p>
        </div>

        <Card className="login-card">
          <div className="login-card-header">
            <Typography.Title level={4} style={{ margin: 0 }}>
              后台管理登录
            </Typography.Title>
            <Typography.Text type="secondary">请输入管理员账号和密码以访问后台</Typography.Text>
          </div>

          <form className="login-card-form" onSubmit={onSubmit}>
            <label className="login-field" htmlFor="login-username">
              <span className="login-field-label">管理员账号</span>
              <Input
                id="login-username"
                autoComplete="username"
                autoFocus
                name="username"
                onChange={(event) => setUsername(event.target.value)}
                placeholder="请输入管理员账号"
                prefix={<UserOutlined />}
                size="large"
                value={username}
              />
            </label>

            <label className="login-field" htmlFor="login-password">
              <span className="login-field-label">密码</span>
              <Input.Password
                id="login-password"
                autoComplete="current-password"
                name="password"
                onChange={(event) => setPassword(event.target.value)}
                placeholder="请输入密码"
                prefix={<LockOutlined />}
                size="large"
                value={password}
              />
            </label>

            {errorMessage ? (
              <Alert showIcon type="error" message={errorMessage} role="alert" />
            ) : null}

            <Button block htmlType="submit" loading={isSubmitting} size="large" type="primary">
              登 录
            </Button>
          </form>
        </Card>

        <p className="login-footer">
          <span>和泰智造</span>
          <span className="login-footer-dot" aria-hidden="true" />
          <span>HOTA MDS v1.0</span>
        </p>
      </div>
    </main>
  );
}
