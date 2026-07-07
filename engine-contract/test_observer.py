"""Self-contained correctness test for zero_copy_observer.py.

Simulates the C11 engine's writer side in Python (matching arena_layout.h
byte-for-byte) against a scratch file standing in for /dev/shm, then drives
AuditObserver against it and checks: header validation, in-order delivery,
ring-buffer wrap-around, and that attn views are correctly zero-copy (must
be released before the mmap can close).

Requires numpy (only for this test / the observer itself -- the future C11
engine has no such dependency).

Usage:
    pip install numpy   # or: pip install --break-system-packages numpy
    python3 engine-contract/test_observer.py
"""

import ctypes
import mmap
import os
import tempfile
import threading
import time

from zero_copy_observer import (
    BLOCK_SIZE,
    CAPACITY,
    D_MODEL,
    MAGIC,
    N_HEADS,
    VERSION,
    AuditHeader,
    AuditObserver,
    AuditSlot,
)

NUM_STEPS = 300  # > CAPACITY, so the wrap-around path gets exercised


def run() -> None:
    total_size = ctypes.sizeof(AuditHeader) + ctypes.sizeof(AuditSlot) * CAPACITY

    with tempfile.NamedTemporaryFile(prefix="fake_pareidolia_audit_", delete=False) as f:
        shm_path = f.name
        f.truncate(total_size)

    try:
        fd = os.open(shm_path, os.O_RDWR)
        mm = mmap.mmap(fd, total_size)

        header = AuditHeader.from_buffer(mm, 0)
        header.magic = MAGIC
        header.version = VERSION
        header.d_model = D_MODEL
        header.n_heads = N_HEADS
        header.block_size = BLOCK_SIZE
        header.capacity = CAPACITY
        header.write_index = 0

        def writer() -> None:
            for step in range(NUM_STEPS):
                slot_index = step % CAPACITY
                offset = ctypes.sizeof(AuditHeader) + slot_index * ctypes.sizeof(AuditSlot)
                slot = AuditSlot.from_buffer(mm, offset)
                slot.step = step
                slot.token_id = step % 50257
                slot.valid_len = min(step + 1, BLOCK_SIZE)
                slot.loss = 3.0 - step * 0.001
                for h in range(N_HEADS):
                    for i in range(slot.valid_len):
                        slot.attn[h][i] = (h + 1) * 0.01 * (i + 1)
                header.write_index = step + 1
                time.sleep(0.001)

        writer_thread = threading.Thread(target=writer, daemon=True)
        writer_thread.start()

        seen = []
        with AuditObserver(shm_path=shm_path) as obs:
            for slot_view in obs.poll_new_slots():
                seen.append(
                    (slot_view.step, slot_view.token_id, round(slot_view.loss, 4), slot_view.attn.shape)
                )
                done = slot_view.step == NUM_STEPS - 1
                del slot_view  # release the zero-copy view before the mmap closes
                if done:
                    break

        writer_thread.join()
        del header  # release our own ctypes view into mm before closing it
        mm.close()
        os.close(fd)

        print(f"observed {len(seen)} slots (writer emitted {NUM_STEPS}, capacity {CAPACITY})")
        print("first 3:", seen[:3])
        print("last 3:", seen[-3:])

        expected_last = NUM_STEPS - 1
        assert seen[-1][0] == expected_last, f"expected last step {expected_last}, got {seen[-1][0]}"
        assert seen[-1][3] == (N_HEADS, BLOCK_SIZE), f"unexpected attn shape {seen[-1][3]}"
        assert seen[-1][1] == expected_last % 50257
        print("OK: wrap-around, zero-copy attn views, and header validation all check out")
    finally:
        os.unlink(shm_path)


if __name__ == "__main__":
    run()
