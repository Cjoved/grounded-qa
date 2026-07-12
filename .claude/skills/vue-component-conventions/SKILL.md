---
name: vue-component-conventions
description: Use this skill when creating or editing Vue components in the Grounded Q&A frontend, or when the user asks about frontend architecture, component structure, or state management patterns.
---

# Vue Component Conventions

## Rules

- Composition API only, `<script setup>` syntax — no Options API
- PascalCase component file names (`ChatPanel.vue`, not `chatPanel.vue`)
- Explicit types in `defineProps` — don't rely on implicit/loose props
- No direct `fetch` calls inside components — always go through
  `src/services/api.js`
- Shared reactive state used by multiple components → a composable in
  `src/composables/`, don't duplicate the logic

## State ownership

- `useAuth` — session/login state, whether the current user is the allowed user
- `useUpload` — upload progress, list of indexed documents
- `useChat` — current conversation, in-flight question, streaming/loading state
- `useEval` — eval run state, latest results

Keep these composables independent of each other — `ChatPanel.vue` shouldn't
need to know about `useUpload` internals, for example. If two composables
need to share data, that's a signal the data belongs in a higher-level
composable instead.

## Citations

Whenever a chat response includes source chunks, render them through
`SourceCitation.vue` rather than inlining citation markup elsewhere — this
keeps the citation UI consistent if the format changes later (e.g. adding
page numbers once Docling bounding-box data is wired in).

## Before adding a new component

1. Check whether an existing component or composable can be extended instead
   of creating something new from scratch
2. Keep components presentational where possible — logic belongs in
   composables, not in component internals
