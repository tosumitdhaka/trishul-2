"""ProtobufSimulator — generates synthetic gNMI-style metric dicts."""
from plugins.shared.simulator_base import SimulatorBase


class ProtobufSimulator(SimulatorBase):
    def _generate_one(self, index: int, source_ne: str = "sim-gnmi-01",
                      domain: str = "PM", **kwargs) -> dict:
        return {
            "source_ne":   source_ne,
            "domain":      domain,
            "metric_name": f"ifInOctets_{index}",
            "value":       float(index * 1024),
            "unit":        "bytes",
            "timestamp":   self.now_iso(),
            "path":        f"interfaces/interface[name=eth{index}]/state/counters/in-octets",
            "encoding":    "JSON_IETF",
        }


protobuf_simulator = ProtobufSimulator()
