from module.plugins.manager import PlugingManager
from module.grpc_client import GRPCClient
from module.config_manager import ConfigManager  # <--- Import mới
import logging
import os

def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Starting monitor agent...")

    # 1. Khởi tạo ConfigManager (kết nối etcd)
    # Nếu chạy trong docker, set ETCD_HOST=etcd trong docker-compose
    config_manager = ConfigManager() 

    # 2. Truyền config_manager vào GRPCClient
    grpc_client = GRPCClient(
        address="localhost:50051", 
        plugin_manager=PlugingManager(),
        config_manager=config_manager
    )
    
    grpc_client.run()

if __name__ == "__main__":
    main()