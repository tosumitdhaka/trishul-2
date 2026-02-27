"""AvroSimulator — generates synthetic Avro-style PM records as dicts."""
from plugins.shared.simulator_base import SimulatorBase


class AvroSimulator(SimulatorBase):
    def _generate_one(self, index: int, source_ne: str = "sim-avro-01",
                      domain: str = "PM", **kwargs) -> dict:
        return {
            "source_ne":   source_ne,
            "domain":      domain,
            "metric_name": f"cpuUsage_{index}",
            "value":       float((index % 100) + 0.5),
            "unit":        "percent",
            "timestamp":   self.now_iso(),
            "schema_id":   "pm-v1",
        }


avro_simulator = AvroSimulator()
