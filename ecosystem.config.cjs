/**
 * PM2：托管 Gunicorn（Django WSGI）。
 * 用法（在仓库根目录）：`pm2 start ecosystem.config.cjs`
 * 请在服务器上配置 DJANGO_SECRET_KEY、DJANGO_ALLOWED_HOSTS（可写在本文件 env 中，或启动前 export 后使用 `pm2 restart hota-mds-api --update-env`）。
 */
const path = require("path");
const root = __dirname;

module.exports = {
  apps: [
    {
      name: "hota-mds-api",
      cwd: path.join(root, "backend"),
      script: path.join(root, "backend", ".venv", "bin", "gunicorn"),
      args: "hota_mds.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120",
      interpreter: "none",
      env: {
        PYTHONUNBUFFERED: "1",
        DJANGO_DEBUG: "0",
        // DJANGO_SECRET_KEY: "在服务器上填写",
        // DJANGO_ALLOWED_HOSTS: "你的域名或IP,127.0.0.1",
      },
    },
  ],
};
