# Veda Book Memory Audit

Date: 2026-08-04
Status: Audit only, no product change in this step

## What I Checked

- uploaded book extraction state
- approved reviewed-memory state
- unified retrieval visibility
- research-mode readiness
- saved chat history persistence

## Main Finding

Veda's earlier refusal to read the uploaded astrology books was not one single problem.
It was a combination of three separate issues:

1. One uploaded PDF was genuinely unreadable at that time.
   - `hindu-predictive-astrology-bv-raman.pdf`
   - stored warning: `PDF had no extractable text. It may be a scanned image.`

2. Other uploaded astrology PDFs were actually extracted successfully.
   - examples found in `data/veda/uploads/*.meta.json`:
     - `predictive-astrology-of-the-hindus-2009nbsped-812083416x-9788120834163_compress.pdf`
     - `Predictive-jyotish-by-m-n-kedaar.pdf`
     - `pdfcoffee.com_predictive-astrology-by-bvbpdf-3-pdf-free.pdf`

3. None of those uploaded books are currently saved as approved durable memory.
   - only one approved reviewed memory exists right now:
     - `data/veda/knowledge_reviews/approved/veda_review_7aa58b0a77ce99ac.json`
     - title: `Banking view`
   - current reviewed-memory JSONL has no saved attachment chunks:
     - `data/intelligence/rag_knowledge/veda_reviewed_documents.jsonl`

That means Veda may have seen uploaded book content in a live chat turn, but it does not currently have those books stored as approved long-term memory.

## Why The Old Refusal Happened

The saved book session still contains the older refusal replies:

- `I cannot read, extract, or analyze the content of the uploaded books...`
- `I can’t read or process uploaded files...`

Those replies are still present inside:

- `data/veda/chat_sessions/1818ed48b6130e41_client_5ce2398d-33f7-4f56-b178-24fbb6c23697/05ed652ad3c51e4a_1785852417046-l6xs9o.json`

But the current chat engine now explicitly tells the model:

- do not claim it cannot read uploaded files when extracted attachment context is available
- use the uploaded material first
- explain that permanent storage still requires reviewed approval

So the older refusal is a saved historical response from the earlier run, not the intended current behavior.

## Practical Scenarios

### Scenario 1: same topic already exists in Veda memory

Current reviewed-memory behavior is:

- Veda checks approved memory first
- if the same readable file is already saved, it recommends `discard`
- if the same topic exists but the new upload adds useful new material, it recommends `merge`
- if the topic is related but still distinct enough, it recommends `save`
- the final choice is still shown to the user in the review panel for confirmation

So Veda now self-decides a recommendation first, then asks for user confirmation before durable save.

### Scenario 2: first-time uploaded book

Current behavior is:

- attachment service extracts text, OCR, and vision summary where possible
- Veda can use that material in the live answer
- the content becomes long-term memory only if the user approves the reviewed save
- once approved, the reviewed note and readable attachment chunks are written to durable storage
- unified corpus + unified BM25 now refresh immediately after that approval

If the user uploads a book but never approves the review, it stays as uploaded file material, not durable Veda memory.

## Research Mode

Current local runtime on 2026-08-04 is ready:

- `VEDA_RESEARCH_ENABLED=True`
- provider: `ddgs`
- `provider_available=True`
- `research_runtime_ready=True`

So research mode is currently available in this runtime.

Why it can still look temporarily unavailable:

- the UI turns research mode off when no live provider is ready
- earlier runs could fail because:
  - the backend started with a Python runtime missing `ddgs`
  - a live DDGS request timed out

The saved book session contains one actual research failure:

- `ddgs_error ... operation timed out`

So "temporary unavailable" can be a real runtime/provider problem even when the feature is enabled in config.

## Chat History

The old chats have not been deleted.

Current backend storage still contains 4 saved sessions under:

- `data/veda/chat_sessions/1818ed48b6130e41_client_5ce2398d-33f7-4f56-b178-24fbb6c23697`

That folder includes:

- the book-learning session
- the `where is my previous chats?` session

Why chats may disappear from the sidebar even though files exist:

- saved chat history is isolated by browser/user owner key
- in auth-off mode that owner key comes from browser local storage client id
- frontend sends that id in `X-Veda-Client-Id`
- if that browser client id changes, the old saved sessions remain on disk but do not load into the new browser identity

## Bottom Line

- uploaded astrology books do exist on disk
- several of them were extracted successfully
- one of them was unreadable in the old run
- the blanket refusal reply was an older behavior gap
- the bigger current reason Veda does not recall those books later is simple:
  - the books were uploaded
  - but they were not approved into durable saved memory
- old chats still exist on disk; if they are missing in UI, the most likely reason is client-id mismatch rather than deletion
