---
name: continuous-learning
description: Extracts reviewable engineering-pattern candidates without silently promoting session output into trusted skills.
---

# Continuous Learning

Use to turn repeated engineering lessons into reviewable candidates for future reuse.

## Trust model

Learning is candidate-based. Session output, model suggestions, shell snippets, and project-specific conventions are untrusted until reviewed. This skill never silently installs a learned skill and never executes learned shell content automatically.

## Candidate categories

- `error_resolution`
- `user_correction`
- `workaround`
- `debugging_technique`
- `project_specific`

Reject simple typos, one-time incidents, stale advice, unsupported guesses, secret-bearing content, and external outages that do not yield a reusable engineering rule.

## Pipeline

1. Extract a concrete pattern from explicit evidence.
2. Normalize it into a short candidate statement.
3. Remove credentials, tokens, private paths, personal data, and unnecessary project specifics.
4. Deduplicate against existing candidates and trusted skills.
5. Assess confidence from repeated evidence, not stylistic certainty.
6. Mark scope as `project` or `general`.
7. Set promotion status to `pending_review`.
8. Require explicit human approval before converting a candidate into a trusted rule or skill.

## Candidate schema

```json
{
  "title": "string",
  "category": "error_resolution|user_correction|workaround|debugging_technique|project_specific",
  "evidence": ["string"],
  "confidence": "low|medium|high",
  "scope": "project|general",
  "contains_sensitive_data": false,
  "promotion_status": "pending_review"
}
```

## Evidence rules

A useful candidate explains what condition triggered the problem, what mechanism caused it, what intervention worked, and what boundaries limit reuse. Prefer repeated evidence across tasks. A single event may remain a low-confidence project candidate but must not be presented as a general rule without support.

## Safety rules

- Never persist raw private transcripts in the public toolkit.
- Never write secrets into candidate files.
- Never promote code that disables security controls or verification gates.
- Never treat a model-generated candidate as trusted evidence by itself.
- Project candidates stay project-scoped unless reviewed and generalized.

## Output contract

Return candidate count, rejected count with reasons, redactions performed, deduplication result, and the exact candidates awaiting review. If nothing is reusable, say so and create no candidate.
