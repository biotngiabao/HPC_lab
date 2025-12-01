from module.plugins.manager import PlugingManager
from module.grpc_client import GRPCClient
from module.config_manager import ConfigManager
from module.command_sync_service import CommandSyncService
import logging
import os

def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Starting monitor agent...")

    config_manager = ConfigManager() 

    if config_manager.is_master_node():
        command_sync_service = CommandSyncService(config_manager=config_manager)
    else:
        command_sync_service = None

    grpc_client = GRPCClient(
        address="localhost:50051", 
        plugin_manager=PlugingManager(),
        config_manager=config_manager,
        command_sync_service=command_sync_service
    )
    grpc_client.run()

if __name__ == "__main__":
    main()