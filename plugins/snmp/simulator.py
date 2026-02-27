"""SNMPSimulator — generates synthetic SNMP trap dicts."""
from plugins.shared.simulator_base import SimulatorBase

TRAP_TYPES = {
    "linkDown":  {"oid": "1.3.6.1.6.3.1.1.5.3", "severity": "CRITICAL"},
    "linkUp":    {"oid": "1.3.6.1.6.3.1.1.5.4", "severity": "CLEARED"},
    "coldStart": {"oid": "1.3.6.1.6.3.1.1.5.1", "severity": "WARNING"},
    "warmStart": {"oid": "1.3.6.1.6.3.1.1.5.2", "severity": "MINOR"},
    "authFail":  {"oid": "1.3.6.1.6.3.1.1.5.5", "severity": "MAJOR"},
}


class SNMPSimulator(SimulatorBase):
    def _generate_one(self, index: int, trap_type: str = "linkDown",
                      source_ne: str = "sim-ne-01", domain: str = "FM", **kwargs) -> dict:
        trap    = TRAP_TYPES.get(trap_type, TRAP_TYPES["linkDown"])
        ifindex = str(index + 1)
        return {
            "agent_address": source_ne,
            "community":     "public",
            "version":       "v2c",
            "trap_oid":      trap["oid"],
            "severity":      trap["severity"],
            "varbinds": [
                {"oid": "1.3.6.1.6.3.1.1.4.1.0", "value": trap_type},
                {"oid": "1.3.6.1.2.1.2.2.1.1",   "value": ifindex},
            ],
            "message":   f"SNMP trap: {trap_type} on {source_ne} if{ifindex}",
            "domain":    domain,
            "source_ne": source_ne,
        }


snmp_simulator = SNMPSimulator()
