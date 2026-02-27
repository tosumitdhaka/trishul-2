"""SFTPWriter — writes encoded bytes to a remote SFTP path."""
from __future__ import annotations
import asyncio
import io
from concurrent.futures import ThreadPoolExecutor

import paramiko

from transformer.base import Writer

_executor = ThreadPoolExecutor(max_workers=4)


class SFTPWriter(Writer):
    """sink_config keys: host, port, username, password|key_path, path."""
    target = "sftp"

    async def write(self, data: bytes | dict, sink_config: dict) -> None:
        import json
        if isinstance(data, dict):
            data = json.dumps(data).encode("utf-8")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _executor,
            self._write_sync,
            data,
            sink_config,
        )

    @staticmethod
    def _write_sync(data: bytes, cfg: dict) -> None:
        host     = cfg["host"]
        port     = cfg.get("port", 22)
        username = cfg["username"]
        path     = cfg["path"]

        transport = paramiko.Transport((host, port))
        if "key_path" in cfg:
            key = paramiko.RSAKey.from_private_key_file(cfg["key_path"])
            transport.connect(username=username, pkey=key)
        else:
            transport.connect(username=username, password=cfg["password"])

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.putfo(io.BytesIO(data), path)
        sftp.close()
        transport.close()
