from typing import Dict

from stacksorbit_dashboard import StacksOrbitDashboard


class EnhancedDashboard:
    def __init__(self, config: Dict, network: str = "testnet") -> None:
        self.config = config
        self.network = network

    def start_dashboard(self) -> None:
        app = StacksOrbitDashboard(config=self.config, network=self.network)
        app.run()
