import etcd3
import json
import time

etcd = etcd3.client(host='localhost', port=2379)
HEARTBEAT_PREFIX = "/monitor/heartbeat/"
CONFIG_PREFIX = "/monitor/config/"

def on_heartbeat_event(watch_response):
    """Theo dõi các node tham gia hoặc rời đi [cite: 174]"""
    for event in watch_response.events:
        key = event.key.decode('utf-8')
        node_id = key.split('/')[-1]
        
        if isinstance(event, etcd3.events.PutEvent):
            print(f"[+] Node {node_id} is ALIVE.")
        elif isinstance(event, etcd3.events.DeleteEvent):
            print(f"[-] Node {node_id} is DEAD (TTL expired).") [cite: 181]

def update_node_config(node_name, interval, metrics):
    """Đẩy cấu hình mới xuống cho một node cụ thể [cite: 104]"""
    key = f"{CONFIG_PREFIX}{node_name}"
    config_data = {
        "interval": interval,
        "metrics": metrics
    }
    # Format config theo yêu cầu bài lab [cite: 209]
    etcd.put(key, json.dumps(config_data))
    print(f"[Server] Pushed config to {node_name}")

if __name__ == "__main__":
    print("Server started. Watching heartbeats...")
    
    # Theo dõi prefix heartbeat
    watch_id = etcd.add_watch_prefix_callback(HEARTBEAT_PREFIX, on_heartbeat_event)
    
    try:
        # Giả lập server console để admin update config
        while True:
            cmd = input("Enter command (update <node> <interval>): ")
            if cmd.startswith("update"):
                _, node, interval = cmd.split()
                # Update metrics mẫu
                update_node_config(node, int(interval), ["cpu", "memory", "disk_io"])
    except KeyboardInterrupt:
        etcd.cancel_watch(watch_id)