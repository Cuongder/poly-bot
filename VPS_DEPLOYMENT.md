# Hướng Dẫn Triển Khai Poly-bot trên VPS Linux

## Yêu Cầu Hệ Thống

- Ubuntu 20.04/22.04 hoặc CentOS 8+
- RAM: Tối thiểu 1GB (khuyến nghị 2GB)
- Disk: 10GB trống
- Python 3.10+
- Node.js 18+
- Domain (tùy chọn nhưng khuyến nghị)

---

## 1. Cài Đặt Môi Trường

### Cập nhật hệ thống
```bash
sudo apt update && sudo apt upgrade -y
```

### Cài đặt Python và dependencies
```bash
# Python
sudo apt install python3 python3-pip python3-venv -y

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Các công cụ cần thiết
sudo apt install git nginx pm2 -y
```

### Cài đặt PM2 (Process Manager cho Node.js)
```bash
sudo npm install -g pm2
```

---

## 2. Clone Repository

```bash
cd /var/www
git clone https://github.com/Cuongder/poly-bot.git
cd poly-bot
```

---

## 3. Cấu Hình Backend

### Tạo virtual environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Cấu hình Private Key

Tạo file `.env.local`:
```bash
nano .env.local
```

Thêm nội dung:
```
PRIVATE-KEY=your_private_key_here
```

**Lưu ý bảo mật:**
```bash
chmod 600 .env.local
```

### Tạo default API key
```bash
python setup_default_key.py
```

### Test chạy backend
```bash
python run_server.py
```

Nếu chạy thành công, nhấn `Ctrl+C` để thoát.

---

## 4. Cấu Hình Frontend

```bash
cd ../frontend
npm install
```

### Build production
```bash
npm run build
```

---

## 5. Cấu Hình PM2 (Production)

### Backend
```bash
cd /var/www/poly-bot/backend
source venv/bin/activate

pm2 start run_server.py --name poly-bot-api \
  --interpreter python3 \
  --log /var/log/poly-bot/api.log
```

### Frontend (Serve bằng PM2)
```bash
cd /var/www/poly-bot/frontend
pm2 serve dist 5173 --name poly-bot-frontend --spa
```

### Lưu cấu hình PM2
```bash
pm2 save
pm2 startup
```

---

## 6. Cấu Hình Nginx (Reverse Proxy)

### Tạo config file
```bash
sudo nano /etc/nginx/sites-available/poly-bot
```

### Nội dung config:

```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;  # Thay bằng domain của bạn

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com;  # Thay bằng domain của bạn

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Kích hoạt site
```bash
sudo ln -s /etc/nginx/sites-available/poly-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 7. Cấu Hình SSL (HTTPS) với Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y

# Tạo SSL cho cả 2 domain
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

---

## 8. Cấu Hình Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 9. Các Lệnh Quản Lý Hữu Ích

### PM2 Commands
```bash
# Xem trạng thái
pm2 status

# Xem logs
pm2 logs poly-bot-api
pm2 logs poly-bot-frontend

# Restart
pm2 restart poly-bot-api
pm2 restart poly-bot-frontend

# Stop
pm2 stop poly-bot-api
pm2 stop poly-bot-frontend

# Xóa khỏi PM2
pm2 delete poly-bot-api
pm2 delete poly-bot-frontend
```

### Cập nhật code
```bash
cd /var/www/poly-bot
git pull

# Restart services
pm2 restart all
```

---

## 10. Backup Database

Database SQLite nằm tại `backend/trades.db`

### Tạo script backup
```bash
sudo mkdir -p /var/backup/poly-bot
sudo nano /usr/local/bin/backup-poly-bot.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /var/www/poly-bot/backend/trades.db /var/backup/poly-bot/trades_$DATE.db
# Giữ lại 7 ngày gần nhất
find /var/backup/poly-bot -name "trades_*.db" -mtime +7 -delete
```

```bash
sudo chmod +x /usr/local/bin/backup-poly-bot.sh

# Thêm vào crontab (chạy mỗi ngày lúc 2AM)
echo "0 2 * * * /usr/local/bin/backup-poly-bot.sh" | sudo crontab -
```

---

## 11. Troubleshooting

### Lỗi port đã được sử dụng
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Lỗi permission
```bash
sudo chown -R $USER:$USER /var/www/poly-bot
```

### Check logs
```bash
# Backend
pm2 logs poly-bot-api

# Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# System
sudo journalctl -u nginx -f
```

### Khởi động lại toàn bộ
```bash
sudo systemctl restart nginx
pm2 restart all
```

---

## 12. Environment Variables Reference

### Backend (.env.local)
```
PRIVATE-KEY=your_private_key_here
JWT_SECRET_KEY=your_jwt_secret_here  # Optional, will auto-generate
```

### Production Build
```bash
cd frontend
VITE_API_BASE_URL=https://api.yourdomain.com npm run build
```

---

## Thông Tin Kết Nối

Sau khi deploy thành công:

- **Frontend**: https://yourdomain.com
- **Backend API**: https://api.yourdomain.com
- **API Docs**: https://api.yourdomain.com/docs

**Default Login:**
- Username: `admin`
- Password: `admin`
- API Key: `demo-api-key-123456789`

---

## Lưu Ý Bảo Mật

1. **Không commit file `.env.local`** - chứa private key
2. **Đổi default API key** sau khi deploy
3. **Sử dụng firewall** để chặn port không cần thiết
4. **Cập nhật regular** để fix security vulnerabilities
5. **Backup database** thường xuyên
