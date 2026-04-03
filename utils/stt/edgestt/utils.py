import time
import hashlib
import uuid
import json
import struct
from typing import Optional
from datetime import datetime, timezone

TRUSTED_TOKEN   = "6A5AA1D4EAFF4E9FB37E23D68491D6F4"
CHANNELS        = 1
BITS_PER_SAMPLE = 16
SAMPLE_RATE     = 16000

class EdgeSTTUtils:
    @staticmethod
    def gen_sec_ms_gec():
        EPOCH = 11_644_473_600
        now   = int(time.time())
        ticks = (now + EPOCH) * 10_000_000
        rounded = ticks - (ticks % 300_000_000)
    
        data   = f"{rounded}{TRUSTED_TOKEN}".encode("utf-8")
        digest = hashlib.sha256(data).hexdigest().upper()
        return digest
    
    @staticmethod
    def get_timestamp():
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def gen_uuid():
        return uuid.uuid4().hex
    
    @staticmethod
    def create_text_message(
        path: str,
        body: dict,
        content_type: Optional[str] = None,
        request_id: Optional[str]   = None,
    ):
        lines = [f"X-Timestamp:{EdgeSTTUtils.get_timestamp()}", f"Path:{path}"]
        if request_id:
            lines.append(f"X-RequestId:{request_id}")
        if content_type:
            lines.append(f"Content-Type:{content_type}")
    
        header = "\r\n".join(lines)
        return f"{header}\r\n\r\n{json.dumps(body)}"

    @staticmethod
    def create_bin_message(
        path: str,
        stream_id: Optional[str],
        request_id: str,
        binary_data: bytes,
        content_type: Optional[str] = None,
    ):
        lines = [f"X-Timestamp:{EdgeSTTUtils.get_timestamp()}", f"Path:{path}", f"X-RequestId:{request_id}"]
        if content_type:
            lines.append(f"Content-Type:{content_type}")
        if stream_id:
            lines.append(f"X-StreamId:{stream_id}")
    
        header_bytes = "\r\n".join(lines).encode("utf-8")
        header_len   = len(header_bytes)
    
        result = struct.pack(">H", header_len) + header_bytes + binary_data
        return result
    
    @staticmethod
    def create_wav_header(sample_rate: int):
        byte_rate   = sample_rate * CHANNELS * (BITS_PER_SAMPLE // 8)
        block_align = CHANNELS * (BITS_PER_SAMPLE // 8)
        data_size   = 0
    
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            data_size + 36,
            b"WAVE",
            b"fmt ",
            16,
            1,
            CHANNELS,
            sample_rate,
            byte_rate,
            block_align,
            BITS_PER_SAMPLE,
            b"data",
            data_size,
        )
        return header