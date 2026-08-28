# Node schema — hermes-ovh-cleanroom map

| Type | Meaning | Lives in |
|---|---|---|
| object | a noun: plane (HES/HPS/HSP), controller, contract file, gate | `objects/<cluster>/` |
| process | a verb: a governed movement through objects | `processes/` |

## Frontmatter fields

- `type`: object | process
- `cluster`: governance | planes | runtime | ops | config | evidence
- `universe`: live | leftover | ghost
- `status`: verified | draft

## Rules

- Cards cite source (`path:line`), never restate it. First-order impact only.
- Claims require evidence refs; the anti-hallucination policy applies to this map too — statuses here cite, they don't assert.
