# Ticket 614: Enable coordination idleTakeover policy in governance manifest

- **ID**: ticket-614
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-25

## Goal and scope

Enable `coordination.idleTakeover` (`enabled: true`, `idleMinutes: 15`, `leaseMinutes: 120`) in `.governance/manifest.json` so `.governance/idle_takeover.py` can perform official CAS lease takeover on stale/expired ticket leases.

## Acceptance criteria

- [x] AC-01: `.governance/manifest.json` enables `coordination.idleTakeover` (`enabled: true`, `idleMinutes: 15`, `leaseMinutes: 120`) and passes `./project/governance-check.sh --actor agent` and `wellman check`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
