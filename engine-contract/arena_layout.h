/*
 * PareidoliaBoricua audit ring buffer — shared-memory ABI.
 *
 * This is intentionally a SEPARATE, small POSIX shared-memory segment from
 * the engine's private 50MB compute arena. The compute arena (weights,
 * activations, KV state) is the C11 engine's own business and may change
 * shape freely; this file is the one thing that must stay byte-stable so
 * the zero-copy Python observer (engine-contract/zero_copy_observer.py) can
 * mmap it from a separate process without coordinating a redeploy.
 *
 * Engine side (writer):
 *   fd = shm_open("/pareidolia_audit", O_CREAT | O_RDWR, 0600);
 *   ftruncate(fd, sizeof(struct pab_audit_shm));
 *   arena = mmap(NULL, sizeof(struct pab_audit_shm), PROT_READ | PROT_WRITE,
 *                MAP_SHARED, fd, 0);
 *
 * Observer side (reader): see zero_copy_observer.py. Read-only mmap, never
 * copies engine memory into a separate buffer before inspection.
 *
 * Concurrency: single-writer / multi-reader SeqLock. The writer fills a slot
 * completely, then increments write_index (release semantics). Readers
 * snapshot write_index before and after reading a slot; if it changed, the
 * writer wrapped into that slot mid-read and the reader must retry.
 */

#ifndef PAB_ARENA_LAYOUT_H
#define PAB_ARENA_LAYOUT_H

#include <stdint.h>

#define PAB_AUDIT_SHM_NAME    "/pareidolia_audit"
#define PAB_AUDIT_MAGIC       0x50414251u /* "PABQ" */
#define PAB_AUDIT_VERSION     1u

#define PAB_D_MODEL           64u
#define PAB_N_HEADS           2u
#define PAB_BLOCK_SIZE        128u
#define PAB_AUDIT_CAPACITY    256u  /* ring buffer slot count, power of two */

#pragma pack(push, 1)

struct pab_audit_header {
    uint32_t magic;         /* PAB_AUDIT_MAGIC, sanity check for the observer */
    uint32_t version;       /* PAB_AUDIT_VERSION, bump on any layout change */
    uint32_t d_model;       /* PAB_D_MODEL, echoed for the observer to assert against */
    uint32_t n_heads;       /* PAB_N_HEADS */
    uint32_t block_size;    /* PAB_BLOCK_SIZE */
    uint32_t capacity;      /* PAB_AUDIT_CAPACITY, number of slots below */
    uint64_t write_index;   /* monotonically increasing; slot = write_index % capacity.
                                Incremented only after the slot is fully written. */
    uint8_t  _reserved[32]; /* pad header to 64 bytes (one cache line) */
};

struct pab_audit_slot {
    uint64_t step;                                  /* absolute generation/audit step */
    uint32_t token_id;                               /* GPT-2 BPE id, 0..50256 */
    uint32_t valid_len;                              /* how many entries per head are
                                                          meaningful: min(step+1, block_size) */
    float    loss;                                   /* streaming online-log-sum-exp CE for this step */
    float    attn[PAB_N_HEADS][PAB_BLOCK_SIZE];      /* causal attention row, current query
                                                          position over its history. Entries at
                                                          index >= valid_len are undefined, not
                                                          zeroed — the observer must slice them off. */
};

struct pab_audit_shm {
    struct pab_audit_header header;
    struct pab_audit_slot    slots[PAB_AUDIT_CAPACITY];
};

#pragma pack(pop)

#endif /* PAB_ARENA_LAYOUT_H */
