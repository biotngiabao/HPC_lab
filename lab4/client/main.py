from module.plugins.manager import PlugingManager
from module.grpc_client import GRPCClient
from module.config_manager import ConfigManager
import logging
import os
import time

def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Starting monitor agent...")

    config_manager = ConfigManager()
    grpc_addr = os.environ.get('GRPC_ADDR', 'localhost:50051')
    retry_interval = int(os.environ.get('RETRY_INTERVAL', '5'))

    while True:
        try:
            logging.info(f"Connecting to gRPC server at {grpc_addr}...")
            grpc_client = GRPCClient(
                address=grpc_addr,
                plugin_manager=PlugingManager(),
                config_manager=config_manager,
            )
            grpc_client.run()
            
            # Nếu run() kết thúc bình thường (không phải exception)
            logging.warning("gRPC connection closed. Reconnecting...")
            
        except KeyboardInterrupt:
            logging.info("Shutting down gracefully...")
            break
        except Exception as e:
            logging.error(f"Error occurred: {e}. Retrying in {retry_interval} seconds...")
        
        time.sleep(retry_interval)

if __name__ == "__main__":
    main()