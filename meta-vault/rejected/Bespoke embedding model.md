---
tags: [rejected]
---

# Bespoke embedding model *(rejected)*

> Could train a custom embedder fine-tuned for debugging conversations.
> Or use a much bigger model (BGE-large, e5-large) for better recall.

## Why no

Two reasons:
1. **`all-MiniLM-L6-v2` is excellent for the cost.** 384-dim, ~25MB,
   CPU-fast, well-understood. The retrieval quality bottleneck in
   memcon is *not* the embedder — it's note quality (which v3.1 fixed
   with [[Why preserve raw context|raw context preservation]]).
2. **Custom embedders are a research project disguised as a feature.**
   Fine-tuning needs labeled data, eval pipelines, drift detection.
   That's months of work to maybe get 5% better recall. Meanwhile the
   feature backlog has [[v4.0 — Knows what it knows (planned)|contradiction detection]],
   the [[VS Code extension|VS Code marketplace publish]], etc. —
   higher-leverage uses of the same time.

If someone wants to swap the embedder, the architecture allows it
([[ingestion.embedder]] is one file). But it's not on memcon's
critical path.

## Related
- [[Sentence Transformers]]
- [[Embeddings]]
- [[Why preserve raw context]]
