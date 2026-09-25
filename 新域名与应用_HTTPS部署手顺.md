# 新域名与应用 HTTPS 部署手顺

> 适用场景：  
> - 应用部署在内部 Linux/Nginx 服务器  
> - 公网 HTTPS 由 FortiGate 处理  
> - Certbot 使用 `webroot` 方式申请 Let's Encrypt 证书  
> - ACME 验证请求通过 FortiGate / 前置设备转发到 Nginx 的 `8088` 端口  
> - 新域名需要最终通过 HTTPS 正常访问

---

## 1. 部署前确认

假设：

```text
新域名：example.com
应用前端目录：/home/user/app/html
ACME 根目录：/home/httpd/app/acme
应用后端：192.168.10.143:8000
```

需要提前确认：

1. 域名 DNS 已解析到正确公网 IP。
2. FortiGate / 前置网络已经允许公网访问该域名。
3. HTTP 的 ACME 请求可以转发到当前 Nginx 的 `8088` 端口。
4. 应用本身已经可以通过内部 HTTP 正常访问。

确认 DNS：

```bash
nslookup example.com
```

---

## 2. 配置 Nginx 应用 HTTP

示例：

```nginx
upstream app_bg {
    server 192.168.10.143:8000 max_fails=1 fail_timeout=10s;
}

server {
    listen 80;
    server_name example.com;

    access_log /var/log/nginx/app.access.log main;

    client_max_body_size 50M;

    location / {
        root /home/user/app/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_redirect off;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";

        proxy_pass http://app_bg;
    }
}
```

配置完成后：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 3. 配置 ACME 8088 验证

创建或复用 ACME 配置文件，例如：

```bash
sudo vi /etc/nginx/conf.d/app-acme.conf
```

内容：

```nginx
server {
    listen 8088;
    server_name example.com;

    root /home/httpd/app/acme;

    location ^~ /.well-known/acme-challenge/ {
        default_type text/plain;
        try_files $uri =404;
    }

    location / {
        return 404;
    }
}
```

如果多个域名共用同一个 ACME 目录，可以写成：

```nginx
server {
    listen 8088;
    server_name example.com example2.com;

    root /home/httpd/app/acme;

    location ^~ /.well-known/acme-challenge/ {
        default_type text/plain;
        try_files $uri =404;
    }

    location / {
        return 404;
    }
}
```

创建目录：

```bash
sudo mkdir -p /home/httpd/app/acme/.well-known/acme-challenge
```

检查 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 4. 测试 ACME 验证链路

创建测试文件：

```bash
echo "acme-test" | sudo tee \
/home/httpd/app/acme/.well-known/acme-challenge/test.txt
```

先测试服务器本机：

```bash
curl -H "Host: example.com" \
http://127.0.0.1:8088/.well-known/acme-challenge/test.txt
```

应该返回：

```text
acme-test
```

再测试公网域名：

```bash
curl http://example.com/.well-known/acme-challenge/test.txt
```

也应该返回：

```text
acme-test
```

只有公网测试成功后，再申请证书。

---

## 5. 使用 Certbot 申请证书

执行：

```bash
sudo certbot certonly \
  --webroot \
  -w /home/httpd/app/acme \
  -d example.com
```

成功后通常会生成：

```text
/etc/letsencrypt/live/example.com/fullchain.pem
/etc/letsencrypt/live/example.com/privkey.pem
/etc/letsencrypt/live/example.com/cert.pem
/etc/letsencrypt/live/example.com/chain.pem
```

确认：

```bash
sudo certbot certificates
```

应看到：

```text
Certificate Name: example.com
Domains: example.com
Certificate Path: /etc/letsencrypt/live/example.com/fullchain.pem
Private Key Path: /etc/letsencrypt/live/example.com/privkey.pem
```

---

## 6. 生成 FortiGate 可导入的 PFX

如果 FortiGate 负责公网 HTTPS，则 Certbot 申请成功后，还需要把证书导入 FortiGate。

推荐生成 Legacy 兼容格式，避免部分 FortiGate 版本出现 PKCS#12 解析错误。

执行：

```bash
sudo openssl pkcs12 -export -legacy \
  -out /home/user/example.com-legacy.pfx \
  -inkey /etc/letsencrypt/live/example.com/privkey.pem \
  -in /etc/letsencrypt/live/example.com/cert.pem \
  -certfile /etc/letsencrypt/live/example.com/chain.pem \
  -name "example.com"
```

输入并记住导出密码。

验证 PFX：

```bash
openssl pkcs12 -legacy \
  -info \
  -in /home/user/example.com-legacy.pfx \
  -noout
```

调整文件权限：

```bash
sudo chown user:user /home/user/example.com-legacy.pfx
chmod 600 /home/user/example.com-legacy.pfx
```

---

## 7. 下载 PFX 到本地

使用 MobaXterm：

1. SSH 登录服务器。
2. 左侧打开 SFTP 文件浏览器。
3. 进入：

```text
/home/user/
```

4. 找到：

```text
example.com-legacy.pfx
```

5. 下载到本地 Windows。

---

## 8. 在 FortiGate 导入证书

FortiGate 中文管理页面：

```text
系统
→ 证书
→ 创建/导入
→ 导入证书
→ PKCS #12 证书
```

上传：

```text
example.com-legacy.pfx
```

输入刚才生成 PFX 时设置的密码。

证书名称建议：

```text
example.com
```

导入完成后，确认证书状态正常。

---

## 9. 在 FortiGate 绑定 HTTPS 证书

进入：

```text
策略与对象
→ 虚拟服务器
```

找到负责该域名公网 HTTPS 的 Virtual Server。

通常需要确认：

```text
类型：HTTPS
外部端口：443
外部 IP：公网 IP
真实服务器：内部应用服务器
SSL 证书：example.com
```

将 SSL 证书选择为：

```text
example.com
```

保存配置。

> 注意：  
> 如果多个域名共用同一个 `公网IP:443` Virtual Server，不要直接用单域名证书覆盖原证书。  
> 这种情况应确认 FortiGate 的 SNI / Virtual Server 配置，或申请包含多个域名的 SAN 证书。

---

## 10. 验证 HTTPS

浏览器访问：

```text
https://example.com
```

命令行验证：

```bash
curl -I https://example.com
```

查看公网实际返回的证书：

```bash
openssl s_client \
  -connect example.com:443 \
  -servername example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

确认：

1. 域名可以正常访问。
2. 浏览器不再提示证书错误。
3. 返回的证书对应 `example.com`。
4. 应用 `/api` 等接口正常。

---

# 日常排查命令

## 查看所有 Nginx 域名配置

```bash
grep -Rni "server_name" /etc/nginx/conf.d 2>/dev/null
```

## 查某个域名配置

```bash
grep -Rni "example.com" /etc/nginx 2>/dev/null
```

## 查 ACME / 8088 配置

```bash
grep -RniE "8088|acme-challenge|well-known" /etc/nginx 2>/dev/null
```

## 确认 8088 监听

```bash
sudo ss -lntp | grep 8088
```

## 检查 Nginx

```bash
sudo nginx -t
```

## Reload Nginx

```bash
sudo systemctl reload nginx
```

## 查看 Certbot 已申请证书

```bash
sudo certbot certificates
```

---

# 标准部署顺序

以后新增域名建议严格按照以下顺序：

```text
1. DNS 配置
        ↓
2. 应用 HTTP / Nginx 配置
        ↓
3. ACME 8088 配置
        ↓
4. 测试公网 /.well-known/acme-challenge/
        ↓
5. Certbot 申请证书
        ↓
6. 生成 -legacy PFX
        ↓
7. MobaXterm 下载 PFX
        ↓
8. FortiGate 导入证书
        ↓
9. FortiGate HTTPS Virtual Server 绑定证书
        ↓
10. HTTPS 验证
```

---

# 本次已验证成功的实际案例

```text
terabox-pub.com
custpro.net
```

ACME 目录：

```text
/home/httpd/tbpub/acme
```

ACME Nginx：

```text
/etc/nginx/conf.d/tbpub-acme.conf
```

配置示例：

```nginx
server {
    listen 8088;
    server_name custpro.net terabox-pub.com;

    root /home/httpd/tbpub/acme;

    location ^~ /.well-known/acme-challenge/ {
        default_type text/plain;
        try_files $uri =404;
    }

    location / {
        return 404;
    }
}
```

应用 Nginx：

```text
/etc/nginx/conf.d/tbpub.conf
```

Certbot：

```bash
sudo certbot certonly \
  --webroot \
  -w /home/httpd/tbpub/acme \
  -d custpro.net
```

证书：

```text
/etc/letsencrypt/live/custpro.net/fullchain.pem
/etc/letsencrypt/live/custpro.net/privkey.pem
```

最终由 FortiGate 负责公网 HTTPS 443 和证书绑定。
