# Proposed Project Timeline

Last updated: 2026-10-07. This proposed schedule uses course weeks and lists tasks and deliverables. It is subject to confirmation by the group and contains no named assignments.

## Milestones

| Milestone | Planned work | Deliverables and completion checks |
|---|---|---|
| Week 4, midweek | Finalise the proposal text, initial analysis figure and references; complete member details in the separate allocation template | Research questions, region, data, background and methods agree; team members complete the allocation table |
| Week 4, end | Review the proposal together, revise, freeze and submit | Check the three-page A4 body plus references, captions, citations and actual allocation; allow at least 24 hours for final checks before submission |
| Week 5, Session 2 | Present the poster covering the region, existing exploration, research questions and proposed method; complete required peer feedback | One poster; feedback on two other groups, with at least one strength and one specific improvement for each; record feedback received |
| Week 5, end | Prepare full trajectories, including positions outside the region; audit the data, split whole drifters 80/20 and construct daily-origin 7-day outcomes | Split IDs, outcome table and exclusion counts; check the 168-hour interval, first exit direction, grounding, missing observations and censoring |
| Week 6, end | Implement training-only merging of 2-degree states and estimate the main transition matrix | State lookup, merge map, support counts and loadable P; check non-negative entries, unit row sums, absorbing states and mass conservation |
| Week 7, end | Complete transport predictions for three starting states and analyse regional connectivity and concentration | 7/28/364-day destination maps, boundary-exit/grounding/remaining/unresolved probabilities and connectivity maps; state long-horizon extrapolation limits |
| Week 8, end | Evaluate on whole held-out drifters and compare against persistence | Top-three coverage, Brier score, usable sample denominators, supported-origin coverage and results aggregated by drifter |
| Week 9, end | Complete drogued-only, 3-day and seasonal comparisons; finalise core results | Support changes, comparable metrics and figures; compare 3-/7-day operators at 21 days; record weak findings and limitations |
| Week 10 | Prepare presentation materials, rehearse and present; draft the final report | Presentation agrees with checked figures; report covers the problem, methods, results, limitations and recommendations |
| Exam period, 3 days before the final deadline | Review the final report together and check reproducibility | Check figures, references, run instructions, operator files, AI-use reflection and the report page limit |
| 24 hours before the final deadline | Freeze the report and deliverables, complete submission checks and submit | Consistent file versions, complete attachments and a saved submission receipt |

## Working Arrangements

- These milestones are proposed, rather than confirmed group agreements. Review deliverables and dependencies for the next stage at the end of each week.
- Official dates for the proposal, poster, presentation and final report follow Moodle and the latest course notices. Bring review and freeze checks forward if an official deadline is earlier than a proposed milestone.
- The poster can present existing data exploration and the research plan before the operator and evaluation are complete. Address feedback in subsequent analysis.
- Prioritise the outcome table, main operator, transport maps and evaluation. Schedule bootstrap, equal-drifter weighting, additional grids and direct multistep validation after the core workflow is stable, while preserving time to review required deliverables.
- This timeline describes planned work. No fitted P, transport predictions or held-out performance results currently exist. See [PROJECT_PROGRESS.md](PROJECT_PROGRESS.md) for the current status.

## Related Files

- [PROPOSAL.md](PROPOSAL.md): Proposal text matching the PDF.
- [TEAM_ALLOCATION.md](TEAM_ALLOCATION.md): Tasks, names, student IDs and target milestones for team members to complete.
- [README.md](README.md): Editable proposal source and repository guide.
