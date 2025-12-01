from module.plugins.manager import PlugingManager
from module.grpc_client import GRPCClient
from module.config_manager import ConfigManager
import logging
import os

def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Starting monitor agent...")

    config_manager = ConfigManager()

    grpc_addr = os.environ.get('GRPC_ADDR', 'localhost:50051')

    grpc_client = GRPCClient(
        address=grpc_addr,
        plugin_manager=PlugingManager(),
        config_manager=config_manager,
    )
    grpc_client.run()

if __name__ == "__main__":
    main()