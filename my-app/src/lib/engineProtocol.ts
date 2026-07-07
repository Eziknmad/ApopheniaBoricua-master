/**
 * Shared types for the PareidoliaBoricua engine <-> frontend wire protocol.
 * Contract: ../../../../engine-contract/WS_PROTOCOL.md
 * Any change here must be mirrored there, and vice versa.
 */

export interface EngineHelloMessage {
  type: "hello";
  model: {
    d_model: number;
    n_heads: number;
    block_size: number;
    vocab_size: number;
  };
  engine_version: string;
}

export interface EngineTokenMessage {
  type: "token";
  step: number;
  token_id: number;
  text: string;
  loss: number;
}

export interface EngineAttnMessage {
  type: "attn";
  step: number;
  heads: number[][];
}

export interface EngineErrorMessage {
  type: "error";
  message: string;
}

export type EngineMessage =
  | EngineHelloMessage
  | EngineTokenMessage
  | EngineAttnMessage
  | EngineErrorMessage;

const KNOWN_TYPES = new Set(["hello", "token", "attn", "error"]);

/** Narrow an untrusted parsed JSON value down to a known EngineMessage, or null. */
export function parseEngineMessage(raw: unknown): EngineMessage | null {
  if (
    typeof raw !== "object" ||
    raw === null ||
    !("type" in raw) ||
    typeof (raw as { type: unknown }).type !== "string" ||
    !KNOWN_TYPES.has((raw as { type: string }).type)
  ) {
    return null;
  }
  return raw as EngineMessage;
}
