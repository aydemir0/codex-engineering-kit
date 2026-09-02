# Performance Rules

- Measure before optimizing; establish a baseline and bottleneck hypothesis first.
- Separate CPU, memory, network, database, and IO constraints.
- Prefer bounded concurrency and explicit backpressure.
- Consider latency distribution, throughput, saturation, and resource cost together.
- Treat database transactions, locks, connection pools, caches, queues, and retries as system behavior.
- Change one meaningful variable at a time and benchmark before/after.
- Re-verify correctness after every performance change.
