from module.plugins.manager import PlugingManager
from module.grpc_client import GRPCClient
import logging


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Starting monitor agent...")

    grpc_client = GRPCClient(address="localhost:50051", plugin_manager=PlugingManager())
    grpc_client.run()


if __name__ == "__main__":
    main()
