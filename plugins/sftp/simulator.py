"""SFTPSimulator — generates synthetic file-based PM records."""
from plugins.shared.simulator_base import SimulatorBase


class SFTPSimulator(SimulatorBase):
    def _generate_one(self, index: int, source_ne: str = "sim-sftp-01",
                      domain: str = "PM", **kwargs) -> dict:
        return {
            "source_ne":   source_ne,
            "domain":      domain,
            "metric_name": f"memUsage_{index}",
            "value":       float(50 + (index % 50)),
            "unit":        "percent",
            "filename":    f"pm_data_{index}.json",
            "timestamp":   self.now_iso(),
        }


sftp_simulator = SFTPSimulator()
