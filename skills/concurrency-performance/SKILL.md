---
name: concurrency-performance
description: Diagnoses concurrency correctness and measured performance bottlenecks before optimizing production systems.
---

# Concurrency and Performance

Use for multithreading, async systems, event loops, worker pools, queues, race conditions, deadlocks, locks, database connection pools, backpressure, CPU/memory bottlenecks, latency, throughput, and distributed coordination.

## Evidence first

For an existing repository, inspect the runtime/language, threading or async model, critical execution paths, shared mutable state, synchronization, queues/workers, database transactions and pools, retries/timeouts, caches, external APIs, metrics, traces, profiling data, and benchmarks before recommending changes.

Do not optimize from intuition alone.

## Correctness before performance

Always consider:

- race conditions, atomicity, visibility, and thread safety;
- deadlocks, livelocks, starvation, ordering, and cancellation;
- idempotency, duplicate execution, retries, and retry storms;
- queue backpressure and resource exhaustion;
- connection-pool exhaustion and transaction duration;
- memory pressure, CPU saturation, IO waits, and overload behavior.

Never trade correctness for speed silently.

## Measurement workflow

1. Establish a measurable baseline.
2. Identify the actual bottleneck.
3. Form a falsifiable hypothesis.
4. Change one meaningful variable at a time.
5. Benchmark before and after.
6. Re-verify correctness.
7. Check regressions and saturation behavior.
8. Record trade-offs.

Separate CPU-bound and IO-bound workloads. Do not introduce concurrency unless it improves a measured constraint. Prefer bounded concurrency over unbounded parallelism.

## Queues and workers

For queues define producer rate, consumer capacity, queue bounds, backpressure, retry/dead-letter behavior, ordering, and idempotency. For worker pools define concurrency limit, scheduling, resource limits, shutdown/cancellation, and error isolation.

## Database concurrency

Inspect transaction duration, isolation level, lock contention, pool sizing, N+1 queries, indexes, long-running queries, retry behavior, and optimistic versus pessimistic locking. Treat transactions and locks as architecture, not local implementation details.

## Recommendation contract

### Current behavior
Observed execution/concurrency model and evidence.

### Bottleneck or correctness risk
Measured problem or concrete failure mode.

### Root cause
Mechanism causing the problem.

### Proposed change
Exact implementation-level change.

### Correctness implications
Race, ordering, atomicity, failure, consistency, and cancellation effects.

### Performance implications
Expected latency, throughput, CPU, memory, and IO impact.

### Complexity
Big O where materially relevant.

### Resource limits
Threads, workers, connections, queue bounds, memory, and other bounded resources.

### Failure behavior
Timeouts, retries, overload, cancellation, and recovery.

### Benchmark strategy
Baseline, workload, metrics, warmup, repetitions, and comparison method.

### Regression strategy
Tests and metrics proving existing behavior remains correct.

### Decision
Adopt, reject, defer, or experiment.

## Rules

- Never claim a performance improvement without measurement.
- Avoid unbounded threads, tasks, queues, connections, or retries.
- Prefer simple concurrency models.
- Consider p50, p95, and p99 latency when distribution matters.
- Consider throughput and saturation together.
- Preserve existing behavior unless a change is justified.
