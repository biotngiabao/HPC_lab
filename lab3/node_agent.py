import time
import json
import etcd3
import threading
import socket

# Kết nối etcd (chỉnh host/port tùy môi trường của bạn, ví dụ forwarding port 2379 ra localhost)
etcd = etcd3.client(host='localhost', port=2379)

HOSTNAME = socket.gethostname() # Hoặc đặt tên cứng như "node-1"
HEARTBEAT_KEY = f"/monitor/heartbeat/{HOSTNAME}"
CONFIG_KEY = f"/monitor/config/{HOSTNAME}"

# Cấu hình mặc định
current_config = {
    "interval": 10,
    "metrics": ["cpu", "memory"]
}

# Lock để đồng bộ hóa việc đọc/ghi config [cite: 204]
# Python threading.Lock đơn giản (đóng vai trò Writer lock)
config_lock = threading.Lock()

def send_heartbeat():
    """Gửi heartbeat với Lease (TTL) [cite: 140, 149]"""
    ttl = 5
    lease = etcd.lease(ttl)
    
    try:
        while True:
            data = json.dumps({"status": "alive", "ts": time.time()})
            # Put key kèm theo lease
            etcd.put(HEARTBEAT_KEY, data, lease=lease) 
            print(f"[Heartbeat] Sent for {HOSTNAME}")
            
            # Refresh lease để giữ key tồn tại [cite: 159]
            lease.refresh()
            time.sleep(ttl / 2) # Sleep ít hơn TTL để đảm bảo refresh kịp
    except Exception as e:
        print(f"Heartbeat error: {e}")

def watch_config_callback(watch_response):
    """Callback khi config trên etcd thay đổi [cite: 117]"""
    global current_config
    for event in watch_response.events:
        if isinstance(event, etcd3.events.PutEvent):
            new_val = event.value.decode('utf-8')
            print(f"[Config] Detected update: {new_val}")
            
            # Cập nhật config với Lock (Writer)
            with config_lock:
                try:
                    current_config = json.loads(new_val)
                    print(f"[Config] Updated successfully: {current_config}")
                except json.JSONDecodeError:
                    print("[Config] Invalid JSON format")

def monitor_loop():
    """Vòng lặp mô phỏng việc giám sát dựa trên config hiện tại"""
    while True:
        # Đọc config với Lock (Reader)
        with config_lock:
            interval = current_config.get("interval", 5)
            metrics = current_config.get("metrics", [])
        
        print(f"[Monitor] Collecting {metrics}. Next run in {interval}s...")
        time.sleep(interval)

if __name__ == "__main__":
    # 1. Bắt đầu lắng nghe thay đổi config
    etcd.add_watch_callback(CONFIG_KEY, watch_config_callback)
    
    # 2. Chạy Heartbeat ở một luồng riêng
    hb_thread = threading.Thread(target=send_heartbeat, daemon=True)
    hb_thread.start()
    
    # 3. Chạy vòng lặp chính (Main thread)
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("Stopping node...")