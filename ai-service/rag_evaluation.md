# Manual RAG Evaluation

## Test Documents

The manual RAG pipeline currently contains three knowledge areas:

- Science Fiction
- Fantasy
- Technology

## Evaluation Results

| # | Question | Expected Answer | Retrieval Correct? | Answer Correct? | Notes |
|---|---|---|---|---|---|
| 1 | Which section contains books about Python? | Technology section | Yes | Yes | Technology document was retrieved first and the answer matched the context. |
| 2 | Which collection contains stories about magic and young wizards? | Fantasy collection | Yes | Yes | Fantasy content contains magic and a young wizard studying at a magical school. |
| 3 | Which collection includes space exploration and wormholes? | Science Fiction collection | Yes | Yes | Science fiction content contains space exploration and a crew travelling through a wormhole. |
| 4 | What topics are covered in the technology section? | Python, software engineering, web development, databases, and artificial intelligence | Yes | Yes | The technology document contains all requested topics. |
| 5 | What is the capital of Japan? | I don't have that information. | Yes | Yes | The question is outside the stored documents and the grounded model correctly refused to use outside knowledge. |

## Failure Analysis

No retrieval or generation failures were observed in this small test set.

The main distinction is:

- A retrieval failure happens when the relevant chunk is not returned by the vector search.
- A generation failure happens when the correct context is retrieved, but the model gives an incorrect or unsupported answer.

## Chunk Size Observation

The current manual pipeline uses:

- Chunk size: 500 characters
- Overlap: 50 characters

For these short documents, each source is small enough that the current chunk size works well.

Reducing the chunk size may create more focused chunks, but it can also remove useful surrounding context if chunks become too small.