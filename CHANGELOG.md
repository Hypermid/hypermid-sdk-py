# Changelog

## 1.1.0

### Added

- **SuperSwap V2 typed fields** (provider == `"superswap"`):
  - `ExecuteResponse`: `source`, `approval_address` (`approvalAddress`),
    `estimated_output` (`estimatedOutput`), `min_output` (`minOutput`),
    `transaction_request` (`transactionRequest`), `v2`.
  - `StatusResponse`: `hyperlane_message_id` (`hyperlaneMessageId`),
    `sub_status` (`subStatus`), `destination_tx_hash` (`destinationTxHash`).

All new fields are optional; LI.FI / NEAR Intents responses are unaffected, and
`sending` / `receiving` status legs remain reachable as dynamic attributes
(models keep `extra="allow"`). `"superswap"` was already an accepted `provider`
value — these additions give it typed, autocompleted access.
