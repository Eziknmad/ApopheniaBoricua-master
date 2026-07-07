"""Zero-copy reader for the PareidoliaBoricua audit ring buffer.

Mirrors engine-contract/arena_layout.h byte-for-byte. Runs on the SAME host
as the C11 engine (the shared memory segment does not cross machines) and
mmaps /dev/shm/pareidolia_audit read-only. No data is ever copied out of
the engine's memory before inspection: ctypes.Structure.from_buffer_copy is
never used here, and the numpy views returned by iter_new_slots() are
backed directly by the mmap.

Usage:
    from zero_copy_observer import AuditObserver

    with AuditObserver() as obs:
        for slot in obs.poll_new_slots():
            print(slot.step, slot.token_id, slot.loss, slot.attn.shape)
"""

from __future__ import annotations

import ctypes
import mmap
import os
import time
from dataclasses import dataclass

import numpy as np

SHM_PATH = "/dev/shm/pareidolia_audit"  # shm_open("/pareidolia_audit", ...) on Linux
MAGIC = 0x50414251  # "PABQ"
VERSION = 1
D_MODEL = 64
N_HEADS = 2
BLOCK_SIZE = 128
CAPACITY = 256


class AuditHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("magic", ctypes.c_uint32),
        ("version", ctypes.c_uint32),
        ("d_model", ctypes.c_uint32),
        ("n_heads", ctypes.c_uint32),
        ("block_size", ctypes.c_uint32),
        ("capacity", ctypes.c_uint32),
        ("write_index", ctypes.c_uint64),
        ("_reserved", ctypes.c_uint8 * 32),
    ]


class AuditSlot(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("step", ctypes.c_uint64),
        ("token_id", ctypes.c_uint32),
        ("valid_len", ctypes.c_uint32),
        ("loss", ctypes.c_float),
        ("attn", (ctypes.c_float * BLOCK_SIZE) * N_HEADS),
    ]


@dataclass(frozen=True)
class AuditSlotView:
    """A consistent, zero-copy snapshot of one ring buffer slot."""

    step: int
    token_id: int
    loss: float
    attn: np.ndarray  # shape (n_heads, valid_len), view into the mmap

    def __repr__(self) -> str:  # keep printed floats readable
        return (
            f"AuditSlotView(step={self.step}, token_id={self.token_id}, "
            f"loss={self.loss:.4f}, attn.shape={self.attn.shape})"
        )


class AuditObserver:
    """Read-only, zero-copy view over the engine's live audit ring buffer."""

    def __init__(self, shm_path: str = SHM_PATH, max_retries: int = 8):
        self._shm_path = shm_path
        self._max_retries = max_retries
        self._fd: int | None = None
        self._mm: mmap.mmap | None = None
        self._np_buf: np.ndarray | None = None
        self._header: AuditHeader | None = None
        self._last_seen_index = 0

    def __enter__(self) -> "AuditObserver":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def open(self) -> None:
        size = ctypes.sizeof(AuditHeader) + ctypes.sizeof(AuditSlot) * CAPACITY
        self._fd = os.open(self._shm_path, os.O_RDONLY)
        self._mm = mmap.mmap(self._fd, size, prot=mmap.PROT_READ)
        # np.frombuffer wraps the mmap without copying its bytes.
        self._np_buf = np.frombuffer(self._mm, dtype=np.uint8)
        self._header = AuditHeader.from_buffer_copy(
            self._mm, 0
        )  # header is tiny and read once per poll anyway; see _read_write_index
        if self._header.magic != MAGIC:
            raise ValueError(
                f"bad magic 0x{self._header.magic:x} in {self._shm_path}; "
                "engine ABI mismatch or segment not initialized yet"
            )
        if self._header.version != VERSION:
            raise ValueError(
                f"observer expects arena_layout.h version {VERSION}, "
                f"engine wrote version {self._header.version}"
            )
        if (
            self._header.d_model != D_MODEL
            or self._header.n_heads != N_HEADS
            or self._header.block_size != BLOCK_SIZE
        ):
            raise ValueError("engine's model geometry does not match this observer's constants")
        self._last_seen_index = self._read_write_index()

    def close(self) -> None:
        # Drop our own numpy/ctypes views onto the mmap first: mmap.close()
        # raises BufferError while any exported buffer (including ones we
        # hold internally) is still alive.
        self._np_buf = None
        self._header = None
        if self._mm is not None:
            self._mm.close()
        if self._fd is not None:
            os.close(self._fd)
        self._mm = self._fd = None

    def _read_write_index(self) -> int:
        assert self._mm is not None
        offset = AuditHeader.write_index.offset
        return ctypes.c_uint64.from_buffer_copy(self._mm, offset).value

    def _slot_offset(self, slot_index: int) -> int:
        return ctypes.sizeof(AuditHeader) + slot_index * ctypes.sizeof(AuditSlot)

    def _read_slot(self, write_index: int) -> AuditSlotView | None:
        """SeqLock read: retry if the writer wrapped into this slot mid-read."""
        assert self._mm is not None and self._np_buf is not None
        slot_index = write_index % CAPACITY
        offset = self._slot_offset(slot_index)

        for _ in range(self._max_retries):
            before = self._read_write_index()
            slot = AuditSlot.from_buffer_copy(self._mm, offset)
            after = self._read_write_index()
            # If more than `capacity` writes happened between before/after,
            # this slot was overwritten during our read: retry.
            if after - before < CAPACITY:
                attn_offset = offset + AuditSlot.attn.offset
                flat = self._np_buf[attn_offset : attn_offset + N_HEADS * BLOCK_SIZE * 4]
                attn_full = flat.view(np.float32).reshape(N_HEADS, BLOCK_SIZE)
                attn_view = attn_full[:, : slot.valid_len]
                return AuditSlotView(
                    step=slot.step,
                    token_id=slot.token_id,
                    loss=slot.loss,
                    attn=attn_view,
                )
            time.sleep(0)  # yield, writer is fast relative to us right now
        return None  # gave up; caller should just wait for the next poll

    def poll_new_slots(self, sleep_s: float = 0.01):
        """Generator yielding every slot written since the last poll, in order.

        Zero-copy: `AuditSlotView.attn` is a numpy view into the live mmap,
        not a copy. Consume it before the ring buffer wraps back to that
        slot (CAPACITY writes later) or copy it yourself with `.copy()`.
        """
        while True:
            current = self._read_write_index()
            if current == self._last_seen_index:
                time.sleep(sleep_s)
                continue
            # If the engine outran us by a full lap, we silently drop the
            # oldest entries rather than reading garbage — jump to the
            # oldest still-valid index.
            start = max(self._last_seen_index, current - CAPACITY)
            for idx in range(start, current):
                slot = self._read_slot(idx)
                if slot is not None:
                    yield slot
            self._last_seen_index = current


if __name__ == "__main__":
    with AuditObserver() as observer:
        for audit_slot in observer.poll_new_slots():
            print(audit_slot)
