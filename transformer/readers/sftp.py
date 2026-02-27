"""SFTPReader — downloads a file from a remote SFTP server (paramiko)."""
from __future__ import annotations
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor

import paramiko

from transformer.base import Reader

_executor = ThreadPoolExecutor(max_workers=4)


class SFTPReader(Reader):
    """source_config keys: host, port, username, password | key_path, path."""
    protocol = "sftp"

    async def read(self, source_config: dict) -> bytes:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            _executor,
            self._read_sync,
            source_config,
        )

    @staticmethod
    def _read_sync(cfg: dict) -> bytes:
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
        buf  = io.BytesIO()
        sftp.getfo(path, buf)
        sftp.close()
        transport.close()
        return buf.getvalue()
