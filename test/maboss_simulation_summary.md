# T-cell marker network — MaBoSS simulation summary

- Network: `Network.sif` / `Network.bnet` (107 nodes, 922 signed interactions),
  built by NeKo from 50 canonical human T-cell marker genes seeded into OmniPath
  (see chat for the gene list and caveats).
- Initial condition: **fully random** — every node set to P(ON)=P(OFF)=0.5,
  independently.
- Simulation: MaBoSS, 5000 Monte-Carlo trajectories, max_time=100, time_tick=1.
- Tracked/output nodes (readout panel): IFNG, IL2, IL4, IL17A, FOXP3, TBX21,
  GATA3, RORC, GZMB, PRF1, CTLA4, PDCD1, CD69.

## Final timepoint — per-node ON probability

| Node  | P(ON) |
|-------|------:|
| PRF1  | 1.000 |
| GZMB  | 1.000 |
| IL17A | 1.000 |
| CD69  | 1.000 |
| TBX21 | 0.964 |
| PDCD1 | 0.731 |
| RORC  | 0.500 |
| IL4   | 0.413 |
| CTLA4 | 0.159 |
| FOXP3 | 0.147 |
| IL2   | 0.000 |
| GATA3 | 0.000 |
| IFNG  | 0.000 |

## Interpretation

Starting from a fully random Boolean state, the network's asymptotic (long-time)
behavior is dominated by a cytotoxic/effector-like attractor: activation marker
CD69 and cytotoxic effectors PRF1/GZMB reach probability 1, alongside the Th1/
cytotoxic master regulator TBX21 (~96%) and the checkpoint receptor PDCD1
(~73%). IL2 and IFNG — canonical Th1 effector cytokines — and the Th2 master
regulator GATA3 are driven to 0, while regulatory (FOXP3, CTLA4) and Th17
(RORC) markers settle at low-to-intermediate probabilities. This reflects the
curated network's wiring (some of it via bridging genes NeKo added to connect
seeds, and default self-regulating rules for genes NeKo could not connect to
regulators) rather than a validated biological claim — see caveats in chat.
