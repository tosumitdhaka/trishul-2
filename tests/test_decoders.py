"""Unit tests for all Transformer decoders."""
import json
import pytest
from transformer.decoders.json import JSONDecoder
from transformer.decoders.csv import CSVDecoder
from transformer.decoders.xml import XMLDecoder
from transformer.decoders.ves import VESDecoder
from transformer.decoders.snmp import SNMPDecoder


# ── JSONDecoder ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_json_decoder_dict_passthrough():
    d = JSONDecoder()
    result = await d.decode({"key": "value"})
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_json_decoder_bytes():
    d = JSONDecoder()
    result = await d.decode(b'{"source_ne": "router-01", "value": 42}')
    assert result["source_ne"] == "router-01"
    assert result["value"] == 42


@pytest.mark.asyncio
async def test_json_decoder_string():
    d = JSONDecoder()
    result = await d.decode('{"domain": "FM"}')
    assert result["domain"] == "FM"


@pytest.mark.asyncio
async def test_json_decoder_invalid_raises():
    d = JSONDecoder()
    with pytest.raises(ValueError, match="invalid JSON"):
        await d.decode(b"not json at all")


@pytest.mark.asyncio
async def test_json_decoder_array_raises():
    d = JSONDecoder()
    with pytest.raises(ValueError, match="expected object"):
        await d.decode(b"[1, 2, 3]")


# ── CSVDecoder ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_csv_decoder_basic():
    d   = CSVDecoder()
    raw = b"source_ne,value,metric\nrouter-01,42.5,ifInOctets\nrouter-02,10.1,ifOutOctets"
    result = await d.decode(raw)
    assert result["count"] == 2
    assert result["rows"][0]["source_ne"] == "router-01"
    assert result["columns"] == ["source_ne", "value", "metric"]


@pytest.mark.asyncio
async def test_csv_decoder_empty_raises():
    d = CSVDecoder()
    with pytest.raises(ValueError, match="empty CSV"):
        await d.decode(b"")


# ── XMLDecoder ─────────────────────────────────────────────────────────────────

XML_SAMPLE = b"""<?xml version="1.0"?>
<alarm>
  <source_ne>router-01</source_ne>
  <severity>CRITICAL</severity>
  <message>linkDown</message>
</alarm>"""


@pytest.mark.asyncio
async def test_xml_decoder_basic():
    d      = XMLDecoder()
    result = await d.decode(XML_SAMPLE)
    assert "alarm" in result
    assert result["alarm"]["source_ne"] == "router-01"
    assert result["alarm"]["severity"]  == "CRITICAL"


@pytest.mark.asyncio
async def test_xml_decoder_invalid_raises():
    d = XMLDecoder()
    with pytest.raises(ValueError, match="parse error"):
        await d.decode(b"<unclosed")


# ── VESDecoder ─────────────────────────────────────────────────────────────────

VES_FAULT_EVENT = {
    "event": {
        "commonEventHeader": {
            "domain": "fault",
            "eventId": "fault0000001",
            "eventName": "Fault_Router_LinkDown",
            "lastEpochMicrosec": 1677000000000000,
            "priority": "High",
            "reportingEntityName": "ems-01",
            "sequence": 1,
            "sourceName": "router-01",
            "startEpochMicrosec": 1677000000000000,
            "version": "4.1",
            "vesEventListenerVersion": "7.2.1",
        },
        "faultFields": {
            "alarmCondition": "linkDown",
            "eventSeverity": "CRITICAL",
            "specificProblem": "Link failure on GigE0/0",
            "faultFieldsVersion": "4.0",
        },
    }
}


@pytest.mark.asyncio
async def test_ves_decoder_fault_event():
    d      = VESDecoder()
    result = await d.decode(VES_FAULT_EVENT)
    assert result["source_ne"]   == "router-01"
    assert result["severity"]    == "CRITICAL"
    assert result["fcaps_domain"] == "FM"
    assert result["alarm_condition"] == "linkDown"


@pytest.mark.asyncio
async def test_ves_decoder_bytes_input():
    d      = VESDecoder()
    raw    = json.dumps(VES_FAULT_EVENT).encode()
    result = await d.decode(raw)
    assert result["source_ne"] == "router-01"


@pytest.mark.asyncio
async def test_ves_decoder_missing_fields_raises():
    d = VESDecoder()
    bad_event = {"event": {"commonEventHeader": {"domain": "fault"}}}
    with pytest.raises(ValueError, match="missing required header fields"):
        await d.decode(bad_event)


@pytest.mark.asyncio
async def test_ves_decoder_domain_mapping():
    d = VESDecoder()
    event = dict(VES_FAULT_EVENT)
    # Override domain to measurement
    event["event"]["commonEventHeader"]["domain"] = "measurement"
    event["event"].pop("faultFields", None)
    result = await d.decode(event)
    assert result["fcaps_domain"] == "PM"


# ── SNMPDecoder ─────────────────────────────────────────────────────────────────

SNMP_TRAP = {
    "agent_address": "192.168.1.1",
    "community":     "public",
    "version":       "v2c",
    "varbinds": [
        {"oid": "1.3.6.1.6.3.1.1.4.1.0", "value": "1.3.6.1.6.3.1.1.5.3"},  # linkDown
        {"oid": "1.3.6.1.2.1.2.2.1.1",   "value": "2"},
    ],
}


@pytest.mark.asyncio
async def test_snmp_decoder_parsed_dict():
    d      = SNMPDecoder()
    result = await d.decode(SNMP_TRAP)
    assert result["source_ne"] == "192.168.1.1"
    assert result["community"] == "public"
    assert "snmpTrapOID"  in result["varbinds"]


@pytest.mark.asyncio
async def test_snmp_decoder_severity_linkdown():
    d    = SNMPDecoder()
    trap = {**SNMP_TRAP}
    trap["varbinds"] = [{"oid": "1.3.6.1.6.3.1.1.4.1.0", "value": "linkDown"}]
    result = await d.decode(trap)
    assert result["severity"] == "CRITICAL"


@pytest.mark.asyncio
async def test_snmp_decoder_severity_linkup():
    d    = SNMPDecoder()
    trap = {**SNMP_TRAP}
    trap["varbinds"] = [{"oid": "1.3.6.1.6.3.1.1.4.1.0", "value": "linkUp"}]
    result = await d.decode(trap)
    assert result["severity"] == "CLEARED"


@pytest.mark.asyncio
async def test_snmp_decoder_json_bytes():
    d      = SNMPDecoder()
    result = await d.decode(json.dumps(SNMP_TRAP).encode())
    assert result["source_ne"] == "192.168.1.1"
