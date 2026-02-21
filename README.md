# Polymarket bot - Optimization with Web Dashboard

Đây là dự án tự động hoá bot giao dịch trên Polymarket (Polygon Mainnet) theo tỷ lệ rủi ro (Risk Management) tối ưu hoá Kelly Criterion và hiển thị dữ liệu qua giao diện React/Vite phong cách Terminal/Dark.

## Yêu Cầu Hệ Thống
- Docker và Docker Compose (Để khởi chạy dễ dàng nhất)
- (Hoặc) Node.js 18+ và Python 3.10+ nếu chạy manual.

## Cài đặt nhanh với Docker

Từ thư mục gốc chứa file `docker-compose.yml`, chạy lệnh sau để build và start toàn bộ hệ thống:

```bash
docker-compose up --build -d
```

- Hệ thống Backend (FastAPI, WebSockets) sẽ chạy trên cổng `:8000`
- Giao diện Web (React, TailwindCSS) sẽ được NGINX phục vụ trên cổng `:80` (Mở trình duyệt xem http://localhost)

## Cấu trúc dự án
- `backend/`: Chứa mã nguồn Python FastAPI.
  - `core/`: Các logic nghiệp vụ chính (RiskManager, FeeOptimizer, SignalGenerator...)
  - `api/`: REST APIs và WebSocket Endpoint
- `frontend/`: Ứng dụng React viết bằng Vite + TailwindCSS.
- `docker-compose.yml`: Triển khai 2 services backend và frontend.

## Testing
Để chạy test cho RiskManager:

```bash
cd backend
python -m unittest tests/test_risk_manager.py
```
