"""XMLDecoder — bytes/str XML → dict via xmltodict."""
import xmltodict
from transformer.base import Decoder


class XMLDecoder(Decoder):
    format = "xml"

    async def decode(self, raw: bytes | str) -> dict:
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        try:
            result = xmltodict.parse(raw, force_list=False)
        except Exception as exc:
            raise ValueError(f"XMLDecoder: parse error — {exc}") from exc
        # xmltodict always returns an OrderedDict with one root key
        # unwrap to get a plain dict
        return dict(result)
