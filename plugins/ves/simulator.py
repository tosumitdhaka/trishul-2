"""VESSimulator — generates synthetic VES 7.x events."""
import time
from plugins.shared.simulator_base import SimulatorBase


class VESSimulator(SimulatorBase):
    def _generate_one(self, index: int, domain: str = "fault",
                      severity: str = "CRITICAL", source_ne: str = "sim-ems-01",
                      **kwargs) -> dict:
        epoch_us = int(time.time() * 1_000_000)
        return {
            "event": {
                "commonEventHeader": {
                    "domain":                  domain,
                    "eventId":                 f"{domain}{index:07d}",
                    "eventName":               f"{domain.capitalize()}_Sim_{source_ne}",
                    "lastEpochMicrosec":        epoch_us,
                    "priority":                "High",
                    "reportingEntityName":      source_ne,
                    "sequence":                index,
                    "sourceName":              source_ne,
                    "startEpochMicrosec":       epoch_us,
                    "version":                 "4.1",
                    "vesEventListenerVersion": "7.2.1",
                },
                **self._domain_body(domain, severity, index),
            }
        }

    @staticmethod
    def _domain_body(domain: str, severity: str, index: int) -> dict:
        sev_ves = {
            "CRITICAL": "CRITICAL", "MAJOR": "MAJOR",
            "MINOR":    "MINOR",    "WARNING": "WARNING",
            "CLEARED":  "NORMAL",
        }.get(severity.upper(), "CRITICAL")

        if domain == "fault":
            return {
                "faultFields": {
                    "alarmCondition":     f"SimAlarm{index}",
                    "eventSeverity":      sev_ves,
                    "specificProblem":    f"Simulated fault #{index}",
                    "faultFieldsVersion": "4.0",
                }
            }
        if domain == "measurement":
            return {
                "measurementFields": {
                    "measurementInterval":      60,
                    "measurementFieldsVersion": "4.0",
                    "nicPerformanceArray":       [],
                }
            }
        return {}


ves_simulator = VESSimulator()
