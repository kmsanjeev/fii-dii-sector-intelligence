# Options and PCR semantics

Stock-option and index-option universes are separate. The current aggregate PCR scope is `ALL_ACTIVE_EXPIRIES`; call/put OI and volume and their ratios are reported independently. A zero or missing call denominator yields null.

The compatibility `market_context.json.pcr` is explicitly labelled `AGGREGATE_STOCK_OPTION_OI_PCR_ALL_ACTIVE_EXPIRIES`, and its signal is `UNINTERPRETED`. Index PCR is exposed separately. Participant-wise options, Greeks and Max Pain are respectively `NOT_SUPPORTED`, `NOT_IMPLEMENTED` and `NOT_IMPLEMENTED`.
