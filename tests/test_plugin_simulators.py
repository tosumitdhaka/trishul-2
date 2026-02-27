"""Unit tests for shared SimulatorBase + all plugin simulators.
   Imports simulators directly — does NOT import plugin.py to avoid ABC instantiation.
"""
import pytest
from plugins.shared.simulator_base import SimulatorBase
from plugins.snmp.simulator import snmp_simulator
from plugins.ves.simulator import ves_simulator
from plugins.protobuf.simulator import protobuf_simulator
from plugins.avro.simulator import avro_simulator
from plugins.sftp.simulator import sftp_simulator


def test_snmp_simulator_batch_count():
    result = snmp_simulator.generate_batch(count=10, trap_type="authFail", source_ne="sw-01")
    assert len(result) == 10


def test_snmp_simulator_all_trap_types():
    for trap in ["linkDown", "linkUp", "coldStart", "warmStart", "authFail"]:
        r = snmp_simulator.generate_batch(count=1, trap_type=trap, source_ne="x")
        assert r[0]["trap_oid"] != ""


def test_ves_simulator_fault_has_fault_fields():
    r = ves_simulator.generate_batch(count=1, domain="fault", severity="MAJOR", source_ne="e1")
    assert "faultFields" in r[0]["event"]


def test_ves_simulator_measurement_has_measurement_fields():
    r = ves_simulator.generate_batch(count=1, domain="measurement", severity="MAJOR", source_ne="e1")
    assert "measurementFields" in r[0]["event"]


def test_protobuf_simulator_has_metric_name():
    r = protobuf_simulator.generate_batch(count=3, source_ne="gnmi-01", domain="PM")
    assert len(r) == 3
    for item in r:
        assert "metric_name" in item
        assert item["source_ne"] == "gnmi-01"


def test_avro_simulator_has_schema_id():
    r = avro_simulator.generate_batch(count=2, source_ne="avro-01", domain="PM")
    assert all("schema_id" in item for item in r)


def test_sftp_simulator_has_filename():
    r = sftp_simulator.generate_batch(count=4, source_ne="sftp-01", domain="PM")
    assert len(r) == 4
    assert all("filename" in item for item in r)


def test_simulator_new_id_is_uuid():
    id1 = SimulatorBase.new_id()
    id2 = SimulatorBase.new_id()
    assert len(id1) == 36
    assert id1 != id2


def test_simulator_now_iso_is_string():
    ts = SimulatorBase.now_iso()
    assert isinstance(ts, str)
    assert "T" in ts
