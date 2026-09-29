# 2026-DATA3001-Yiyuan Xie-Group2
--- 
## Research questions and objectives

**Project.** "Where things end up" (Project 3.2.2 (Transport)): a surface-transport operator for the Agulhas Current region R, defined in Section 2.

**Aim.** When something is lost at sea, such as a person in a life raft, an oil slick or floating debris, responders need to know where it is likely to drift. We will build a transition matrix that estimates where surface drifters starting anywhere in R are found after a week, a month and a year, and where they eventually leave the region. The product describes the movement of near-surface water as sampled by drogued drifters; applying it to particular floating objects would need extra assumptions about wind and waves.

**Primary question.** How do starting locations in R affect westward versus eastward destinations? South of Africa the current turns back east, while some water enters the Atlantic.

- **RQ1: Where things end up.** Something goes into the water at a chosen point in R, such as a container off a ship, a life raft or a slick of oil. Where has the surface flow taken it a week later, a month later, and a year later? We answer this for three supported starting cells.
- **RQ2: Connectivity.** At the scale of the whole box, which parts of R feed which others, and which are cut off from the rest? Where does R as a whole gather material, and where does it lose it?
- **RQ3: Reliability.** How well do predicted destinations match observed destinations for held-out drifters? How sensitive are the results to the chosen interval, to drogue status and to season?

**Objectives.**

- **1. Data.** Preserve drifter identity and timestamps, including the observations outside R that are needed to establish destinations. Count the usable endpoint pairs and the distinct drifters per starting cell. Separate observed exits from missing future observations.
- **2. Transition matrix.** Estimate $P_{ij} = \Pr(X_{t+7\ \mathrm{days}} \in j \mid X_t \in i)$ from observed endpoint pairs on 2° cells, with an absorbing outside-region state that represents the first recorded exit. Combine poorly supported cells.
- **3. Product.** Deliver a transition matrix that someone else can pick up and iterate forward, together with what it says about where the chosen release points end up, and about where R as a whole gathers material and where it loses it.
- **4. Validation.** Split training and evaluation data by drifter, and compare predicted with observed destinations for the held-out drifters.
- **5. Sensitivity.** Test how sensitive the results are to the chosen interval. Account for drogue status, because drifters that have lost their drogue have velocities contaminated by wind slip. Inspect seasonal coverage before pooling transitions.
- **6. Region-independence.** Nothing in the code depends on the exact R, so all functions work when given a different region.

--- 
## Data/region and data description
---
## Why that problem is important/significant
---
## Intro/background and existing studies/solutions
---
## Proposed method
--- 
## Initial analysis and visualization
--- 
## Timeline and plan
--- 
