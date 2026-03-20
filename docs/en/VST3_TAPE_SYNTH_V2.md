# ACE-Step VST3 Tape Synth V2 Product Spec

This document defines the product structure for the post-MVP ACE-Step VST3 plugin tracked by
epic `#903` and issue `#904`.

It is the source of truth for the V2 interaction model and should be used to guide implementation
PRs `#905` through `#909`.

## Summary

V2 evolves the current ACE-Step VST3 MVP from a prompt-and-preview utility into a
**future-facing hardware synth + magnetic tape workstation**.

The plugin should feel like an instrument, not a web form embedded in a DAW:

- a central tape transport for generation, playback, compare, and take navigation
- hardware-style engine modules around the transport
- project and composition tools in a dedicated lane
- results treated as first-class musical takes, not a single temporary file

The V2 implementation must build on the already-merged MVP foundation:

- keep the existing backend/API path
- keep preview playback and file handoff working
- preserve DAW project persistence
- expand structure and capability without regressing the current generate-preview workflow

## Product Goals

V2 should solve these user needs inside the DAW:

- generate from text without leaving the session
- compare multiple results quickly like auditioning takes
- switch between generation modes without changing tools
- treat LoRA, conditioning, and composition controls as instrument features
- preserve project context when the DAW session is reopened

The plugin should not try to clone the AceFlow web UI. It should adapt the spirit of `#799` into a
plugin-native instrument workflow.

## Non-Goals

These are out of scope for the initial V2 phases unless a later issue explicitly reopens them:

- embedding inference inside the plugin process
- replacing the existing backend protocol from scratch
- AU, CLAP, or AAX support
- drag-and-drop timeline integration before the transport and results model are stable
- a full browser-style project manager inside the plugin

## Source Of Truth And WIP Policy

`codex/tape-synth-v2-wip` is an exploratory branch only.

Use it as reference for:

- background painting and faceplate ideas
- look-and-feel experiments
- naming and layout inspiration

Do not use it as a merge base or PR head branch. Every V2 PR must start from `origin/main` and
selectively port only the relevant pieces.

## Core Metaphor

The ACE-Step V2 plugin is a **tape-synth workstation**.

This metaphor has three layers:

1. **Synth brain**
   Engine, mode, LoRA, conditioning, and quality controls.
2. **Tape transport**
   Generate, queue, render, compare, preview, and take switching.
3. **Composition lane**
   Project context, prompt, lyrics, sections, chords, and export concepts.

The tape transport is the primary interaction surface. This is the center of the plugin visually
and behaviorally.

## Information Architecture

The V2 UI is divided into five fixed surfaces.

### 1. Top Strip

Purpose:

- identify the product
- show preset/session context
- expose backend and engine state at a glance

Contents:

- product badge and version
- session or preset name
- backend lock/status lamp
- active mode label
- engine/model label

### 2. Tape Transport

Purpose:

- serve as the primary control center for render and audition workflows

Contents:

- generate / cancel / compare transport buttons
- tape-style status display
- active take selector
- queued/running/completed transport state
- progress and warning display
- take count and compare state

This surface owns the user's main action loop:

`configure -> generate -> watch progress -> audition -> compare -> hand off`

### 3. Synth Brain

Purpose:

- hold generation controls that behave like instrument parameters

Contents:

- duration
- seed
- engine/model
- quality
- generation mode
- LoRA section
- conditioning section

This surface should be modular and hardware-like, not form-like.

### 4. Results Deck

Purpose:

- treat outputs as durable takes instead of one-off files

Contents:

- take list
- metadata strip
- compare pairing controls
- preview source and file status
- reveal/export controls

Each take should expose:

- label
- seed
- model
- quality
- duration
- status text
- remote URL
- local preview file path
- compare grouping when present

### 5. Composition Lane

Purpose:

- contain project-level creative context

Contents:

- prompt
- lyrics
- section list
- chord progression
- project/session metadata
- export concepts

This lane may be tabbed or collapsible, but it must have a defined home in the plugin from Phase 1.

## Default Layout

The default desktop layout should be:

- top: brand / preset / status strip
- center: tape transport as the main visual anchor
- left: composition lane
- right: synth brain
- bottom: results deck and preview transport

On tighter plugin widths:

- composition lane becomes tabbed
- results deck collapses into a take browser + metadata display
- tape transport remains centered and visually dominant

## Primary User Flows

### Flow 1: Text Generation

1. Open session or restore existing DAW project state.
2. Adjust prompt, lyrics, and engine settings.
3. Press generate on the tape transport.
4. Watch queued/rendering state in the transport display.
5. When complete, audition the resulting take in the results deck.
6. Reveal or hand off the file if desired.

### Flow 2: Take Audition And Compare

1. Generate or load multiple takes.
2. Choose a take from the results deck.
3. Preview it through the plugin transport.
4. Enable compare mode and pair takes A/B.
5. Switch between compare partners from the transport or result controls.

### Flow 3: Mode-Based Generation

1. Choose generation mode from the synth brain.
2. The synth brain exposes only the controls needed for that mode.
3. The transport still owns generation and progress.
4. The results deck still owns preview and compare.

### Flow 4: Session Restore

1. Reopen a DAW project.
2. Restore the last session state, selected take, and mode.
3. Restore result metadata even if the backend is offline.
4. Show clear missing-file or offline state without breaking the plugin editor.

## Mode Model

V2 supports four generation modes, all surfaced through one common transport:

- `text`
- `reference`
- `cover_remix`
- `custom_conditioning`

Rules:

- mode selection lives in the synth brain
- mode changes affect visible controls and request-building behavior
- mode does not move the transport or results surfaces
- unsupported fields for the active mode must be hidden or disabled, not silently ignored

## AceFlow Mapping From PR #799

The V2 plugin adapts these AceFlow-inspired capabilities:

- richer result metadata -> results deck metadata strip
- compare flow -> tape transport + result deck compare pairing
- LoRA workflow -> synth brain LoRA module
- conditioning modes -> mode switch + conditioning module
- project/session context -> composition lane
- chord / section concepts -> composition lane subsections

The plugin must not mirror AceFlow page structure. It should map the same intent into persistent
instrument surfaces.

## V2 State Model

The V2 state must extend the current plugin state into a session/workstation model.

### Transport State

Supported states:

- `idle`
- `submitting`
- `queued`
- `rendering`
- `succeeded`
- `failed`
- `compare_ready`

### Session State

Must persist:

- selected mode
- prompt and lyrics
- engine controls
- LoRA selections and weights
- conditioning state
- selected take
- compare state
- section/chord/project context

### Result State

Each result take must support:

- take id or slot id
- display label
- backend task relation
- seed
- model
- quality
- duration
- status text
- remote file URL
- local preview path
- compare pairing metadata

## Phase Breakdown

### Phase 1: Product Spec And Interaction Model

Issue: `#904`

Deliverables:

- this product spec
- locked information architecture
- locked transport metaphor
- clear mapping from MVP and `#799` into V2 surfaces

No code changes beyond documentation.

### Phase 2: Design System And Component Rewrite

Issue: `#905`

Deliverables:

- `V2LookAndFeel`
- modular editor components
- tape transport visual system
- hardware-style module shells

This phase should re-skin and re-structure the UI while still using MVP behavior underneath.

### Phase 3: Workflow Backbone

Issue: `#906`

Deliverables:

- upgraded session state
- richer result model
- transport state machine
- compare-ready result handling

This phase gives the plugin an extensible internal model before broader feature expansion.

### Phase 4: Generation Modes

Issue: `#907`

Deliverables:

- mode switch
- conditioning panels
- mode-aware request building

### Phase 5: LoRA And Compare

Issue: `#908`

Deliverables:

- LoRA catalog UX
- weight controls
- A/B compare workflow

### Phase 6: Composition Tools

Issue: `#909`

Deliverables:

- section lane
- chord progression support
- project/session composition context

## Component Targets For Implementation

The V2 editor rewrite should be componentized into at least:

- `StatusStripComponent`
- `TapeTransportComponent`
- `SynthPanelComponent`
- `ResultDeckComponent`
- `PreviewDeckComponent`

Additional helper components are expected for:

- mode tabs
- LoRA controls
- section/chord editors
- metadata display rows

## Backend And Processor Guidance

V2 should preserve the existing backend path:

- `GET /health`
- `POST /release_task`
- `POST /query_result`

Implementation guidance:

- do not replace the current API contract unless a later issue explicitly requires it
- introduce mode-aware request building as a layer on top of current backend integration
- keep all network and long-running operations off the audio thread
- separate processor responsibilities into focused helpers over time:
  - task management
  - result management
  - preview management
  - compare management

## QA And Acceptance Criteria

Every V2 PR must:

- build independently from `origin/main`
- load in Reaper on macOS
- preserve the existing MVP generate-preview-reveal path
- keep DAW save/reopen working
- avoid relying on `codex/tape-synth-v2-wip`

`#904` is complete when:

- every major user-facing function has a defined home in the UI
- the tape transport metaphor is locked
- the next implementation PRs do not need to invent product structure
- V2 phases `#905` through `#909` have clear boundaries
