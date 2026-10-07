# Project Progress and Work Log

Last updated: 2026-10-07, Australia/Sydney.

## Working Agreements

- Use local `muyao` as the baseline, at commit `8d0e006` (2026-09-24).
- Following the group's decision on 2026-10-06, use the locally saved Lucy plan (`origin/lucy`, `4e3d1ef`) as the main method and integrate it into the `muyao` working tree. Adopting the plan does not mean switching or merging branches.
- Do not `pull` or `fetch` for this task. Use locally saved references for analysis; check remote refs only to verify the explicitly requested push.
- Never `push` without explicit user permission. On 2026-10-07, the user explicitly authorised committing the prepared documents to `muyao` and pushing that branch over SSH. Earlier entries describe the work before this authorisation.
- Maintain this file whenever work is performed: update section status, then append changes, verification and remaining issues.
- A completed proposal manuscript does not mean the model has been implemented or research conclusions validated.
- Maintain all project Markdown documents in English, as requested on 2026-10-07.

## Current Section Status

This table follows the reordered [README.md](README.md), using Lucy's content order. Original muyao Sections 3/4 now correspond to Sections 1/5. Historical logs retain the old numbering.

| Section | Previous state | Current status | Evidence and remaining work |
|---|---|---|---|
| 1. Research questions and objectives | Original Section 3 had a draft | Proposal text complete | Aim, RQ1-RQ3, deliverables, acceptance criteria and 7/28/364-day horizons are specified. |
| 2. Data/region and data description | Region and counts documented; conventions needed alignment | Proposal text complete | Region, version, access date, time range, trajectory structure, variables and full-track loading are specified; candidate-region counts were checked offline using consistent boundaries. |
| 3. Why this problem is important | Material existed in original Section 1 | Proposal text complete | Scientific and applied importance, client use, probabilistic outputs, drifter/object differences and boundary-proxy limitations are explained. |
| 4. Background and existing studies | Lucy had a draft; no separate muyao section | Proposal text complete | Mean/seasonal flow, retroflection variability and the closest transition-matrix study are integrated; full text and citation metadata were checked; contribution and comparability limits are stated. |
| 5. Proposed method | Original Section 4 aligned with Lucy | Proposal text complete | Audit, split, daily timestamp pairing, first events/censoring, support/merging, pooled P, propagation, evaluation and sensitivities are specified; details are in TRANSPORT_METHOD. |
| 6. Initial analysis and visualization | Notebook material remained on Lucy's branch | Text and figure integrated | Local Lucy notebook archived; three saved figures extracted; spatial, annual/seasonal, drogue and termination statistics integrated. These are exploratory evidence, not model performance. |
| Proposed timeline (unnumbered) | Original Section 5 was blank | Allocation removed from proposal; timeline retained | The user requested removal of the allocation section from the PDF. TEAM_ALLOCATION.md remains a separate blank template; PROJECT_TIMELINE.md lists tasks and completion checks without named assignments. |

Current stage: Sections 1-5 and the initial analysis are written in Lucy's order. The user requested removal of the allocation section from the proposal; a separate blank template remains for team members. Missing names do not block the requested manuscript edits. The schedule uses course weeks. Client/assessment/repository metadata and internal audit commentary have been removed. PROPOSAL.md matches the PDF source; the revised PDF omits allocation and retains the timeline, with three A4 body pages plus one references page and all four pages visually checked. All six project Markdown files are in English. Research implementation remains outstanding: no transition matrix, release-transport predictions or held-out performance results exist.

## Following Lucy's Plan: Decisions and Next Steps

The main question remains: compare coastal-current, retroflection and return-current starting states, then study destinations, regional connectivity and predictive reliability. The workflow is daily origins -> 7-day first-event outcome table -> 2-degree grid with sparse-neighbour merging -> row-normalised P -> P/P^4/P^52 -> whole-drifter evaluation and sensitivity analysis.

### Three Method Choices Aligned

| Item | Muyao method on 2026-10-05 | Current plan following Lucy |
|---|---|---|
| Sparse cells | No merging; unsupported destinations enter unresolved | Merge adjacent observed cells using training usable-outcome support; only residual unsupported destinations enter the unresolved diagnostic. |
| Probability estimation | Equal weight per drifter | Pool usable transition counts and normalise each origin row; equal-drifter weighting is supplementary. |
| Main evaluation | Brier primary, top-three secondary | Top-three destination coverage against persistence; supplementary Brier; geographic destinations and absorbing states reported separately. |

Retain necessary implementation clarifications: pair by timestamps, not fixed row offsets; split whole drifters before defining support, merges or releases; retain the first exit even if a drifter returns; distinguish grounding from lost transmission; P^4/P^52 represent 28/364 days. East/west exits are directional proxies, not the literature's interocean leakage percentages.

Lucy specified merging with neighbours without choosing an algorithm. [TRANSPORT_METHOD.md](TRANSPORT_METHOD.md) proposes a deterministic, training-only shared-edge rule. Inspect merge maps and spatial resolution after implementation. This rule is our proposed detail, not an existing Lucy implementation.

### Execution Order and Deliverables

| Order | Work | Completion evidence | Current status |
|---|---|---|---|
| 1 | Integrate proposal and existing exploration | Annual, seasonal, drogue and termination evidence; figures and literature; blank allocation template and proposed schedule; page-limit check | Text, evidence, references and templates complete; revised PDF has three body pages and passes visual review. |
| 2 | Implement trajectory pairing | Split IDs and daily-origin outcome table, including exit direction, grounding, censoring and exclusion reasons; timestamp/event checks | Not implemented. NPZ lacks time series and cannot directly support pairing. |
| 3 | Estimate main operator | Training merge map, state lookup, support and P; non-negative entries, unit row sums and mass conservation | Not implemented. |
| 4 | Answer RQ1/RQ2 | Three supported release states; 7/28/364-day maps; exit/grounding/remaining/unresolved probabilities; connectivity and concentration maps | Not implemented. |
| 5 | Answer RQ3 | Whole-drifter 20% test set; top-three/persistence and coverage; drogued-only, 3-day and seasonal comparisons | Not implemented. |
| 6 | Package deliverables and extensions | Reproducible instructions, loadable operator and figures; supplementary weighting, probability scoring, direct multistep checks and bootstrap as appropriate | Not implemented. |

Lucy originally had five proposal headings: research questions, data/region, importance, background and method. These now form Sections 1-5, with Section 6 for initial analysis and an unnumbered team plan. The numbering map appears below.

The nearest code milestone is **an outcome table and a verifiable 7-day main operator**. Method text and occupancy statistics cannot establish that the model is complete. Run the core analysis before extensions.

## Local Branch Comparison

| Locally saved reference | Ahead of muyao | Behind muyao | Additional content |
|---|---:|---:|---|
| origin/muyao (`8d0e006`) | 0 | 0 | Baseline. |
| origin/lucy (`4e3d1ef`) | 20 | 0 | Expanded research questions, importance, literature and method; annual/seasonal, drogue and termination notebook checks with saved figures. |
| origin/vrishin (`b0de117`) | 3 | 0 | CloudDrift scripts, data audit, 7-day pairing-feasibility and coverage plotting code, integrated proposal draft. |
| origin/main (`df5536b`) | 4 | 12 | Diverged from muyao; README has only a title. It is not a newer branch containing all muyao work. |

Lucy and vrishin have 20 and 3 unique commits respectively. Vrishin's text cites some Lucy results without merging her expanded notebook. Their committed work has not been unified into muyao.

### Proposal Numbering Map

This map explains historical entries; current completion status is at the top.

| Current content | Original muyao content | Integration |
|---|---|---|
| Section 1: Research questions and objectives | Section 3 | Retain and condense questions and scope. |
| Section 2: Data/region and data description | Sections 1-2 | Add structure/variables, time range and consistent candidate-region comparison. |
| Section 3: Why this problem is important | Section 1 | Separate scientific and applied importance. |
| Section 4: Background and existing studies | Part of Section 1 plus Lucy review | Add method evidence, contribution and literature comparison. |
| Section 5: Proposed method | Section 4 | Retain Lucy's main plan and implementation clarifications. |
| Section 6: Initial analysis and visualization | Section 2 evidence plus Lucy notebook | Integrate adequacy and initial findings with provenance. |
| Proposed timeline | Section 5 | Proposed milestones retained; actual allocation omitted from the proposal and kept in a separate blank template. |

## Verified Data Evidence

- Region: 10-45 degrees E, 45-20 degrees S; NOAA GDP hourly v2.01.1.
- Saved CloudDrift notebook: 3,848,969 hourly records and 1,149 distinct trajectories.
- Cache/JSON: 3,848,967 records; the two-record difference follows documented boundary conventions.
- At 2 degrees: 178/234 cells occupied, 171 with at least 10 distinct drifters, median 116 per occupied cell.
- Offline recounts from [gdp_1deg_grids.npz](gdp_1deg_grids.npz) reproduce regional records, drifters and 2-degree statistics in [region_adequacy_results.json](region_adequacy_results.json).
- [section2 .ipynb](section2%20.ipynb) retains original CloudDrift counts, 1-degree coverage and Benguela comparison; [analysis/section2_lucy.ipynb](analysis/section2_lucy.ipynb) archives the locally saved expanded Lucy notebook.
- Recounting the proposal's Benguela box (0-20 degrees E, 38-15 degrees S) gives 2,538,266 records and 706 drifters, matching Lucy's saved output. The original JSON's different box is retained and distinguished.
- [analysis/proposal_evidence.json](analysis/proposal_evidence.json) stores recounts, original outputs and figure provenance/hashes. Full GDP data were not downloaded again and the analysis notebook was not executed.

## Overall Assignment Requirements

Sources: [2026 course introduction](../intro.pdf), [GDP project brief](../gdp-overview.pdf) and [data-science project workflow](../unsw-DATA3001-steps.pdf).

| Deliverable | Weight | Timing and requirements |
|---|---:|---|
| Project proposal / README | 15% | Week 4; three A4 pages plus references; questions, importance, methods, regional data adequacy, initial results and explicit allocation. |
| Poster session | 20% | Week 5, Session 2; one poster per group; evaluate two other groups, with at least one strength and one specific improvement in each review. |
| Presentation | 25% | Week 10; group 10% plus individual 15%; 2026 introduction provisionally specifies 15-20 minutes, with final details to follow. |
| Final report | 40% | Exam period; one report per group, maximum 30 pages; reflect on AI's role in the final product. |

Selected project: **3.2.2: Where things end up**. Deliver a surface-transport operator others can load and iterate, destination distributions from selected releases, and regional connectivity, concentration and loss analysis. Justify the region using data and scientific/economic reasons; support other regions through configuration. The five suggested starting directions need not all be completed.

The generic workflow is a 2022 document; its 12-minute presentation differs from the 2026 introduction. Use 2026 materials and the latest Moodle notices for timing and assessment. Suggested report content includes executive summary, background, scope, plan, findings and recommendations, explaining decisions with evidence.

## Outstanding Work and Priorities

1. **Implement and validate current Section 5.** Daily UTC-midnight origins, timestamp pairing, first events, whole-drifter split, training support/merging, pooled matrix and top-three/persistence are the main workflow. Build outcomes from timed trajectories before estimation/evaluation; the current NPZ contains coverage only. Weighting extensions and uncertainty follow the core workflow.
2. **Team members complete actual allocation separately.** The user requested removal of the allocation section from the proposal. [TEAM_ALLOCATION.md](TEAM_ALLOCATION.md) remains available with blank tasks, names, IDs, deliverables, milestones and review fields; do not infer assignments from branches/authors. See [PROJECT_TIMELINE.md](PROJECT_TIMELINE.md).
3. **Count conventions aligned.** README uses offline-verified candidate-region counts under common boundaries. The original JSON's Benguela box remains historical evidence and must not be mixed with the proposal box.
4. **Check results before integrating other branches.** Vrishin's README calls 190 grounding and 857 transmission-loss cases regional endings; Lucy's notebook gives 70/203 ending inside, with the remaining cases belonging to all entering tracks. Vrishin's new audit/pairing outputs are not saved in tracked JSON.
5. **Figures and references integrated.** Three saved figures extracted, coverage figure included, McAdam reference added; public Crossref/DataCite metadata and McAdam full text checked. Literature percentages are not numerical targets for this model.
6. **Recheck layout after edits.** Current [output/pdf/proposal.pdf](output/pdf/proposal.pdf) has three A4 body pages plus one references page and passes visual review. Adding actual allocation or changing proposal text requires export and inspection again.

## Work Log

### 2026-10-02: Branch and Document Inspection

- Switched from clean main to muyao, creating a local tracking branch; did not merge other branches.
- Read three PDFs, branch READMEs, scripts, statistics JSON and saved notebook results.
- Compared commit history and branches; recounted core statistics offline from the existing NPZ.
- Before the user prohibited remote attempts, fetch succeeded under full access and pull --ff-only returned Already up to date. All subsequent work uses local files/references.

### 2026-10-02: Advance Original Section 3

- Replaced four draft bullets with a complete project definition: main question, RQ1-RQ3, five objectives, deliverables and acceptance criteria.
- Integrated Lucy/vrishin intentions into muyao's structure without merging branches or copying unchecked results.
- Specified P^4/P^52 as 28/364 days, rather than exact 30/365-day periods.
- Clarified first-exit absorption, directional boundaries, grounding/censoring and drogue loss versus termination.
- Added whole-drifter evaluation, uncertainty, reproducibility and configurable-region objectives as planned work.
- Corrected the header's Week 3 to confirmed Week 4 and updated its repository link; exact submission time still required Moodle.
- Created this progress document with sections, branches, requirements, issues and next steps.
- Verification: git diff --check passed; original Sections 1/2/4/5 matched baseline; Section 3 contained questions, objectives and acceptance criteria. Offline statistics matched: 3,848,967 records, 1,149 drifters, 178 occupied 2-degree cells, median 116, 171 cells with at least 10 drifters.
- Scope: document structure/diff/cache checks only; no model training or full download. README had about 1,561 whitespace-separated items including references/tables; final three-page layout not yet verified.
- Result: original Section 3 text complete; Section 4 method/implementation and Section 5 allocation remained outstanding. Changes stayed local on muyao; no commit, merge or push.
- Temporary files: 57 input-PDF previews retained outside the repo in ../tmp/pdfs/ because cleanup was blocked by execution policy.

### 2026-10-05: Improve Original Section 3 and Complete Section 4 Method Text

- Scope: improve proposal Section 3 and finish Section 4 against local muyao; no remote reads, pull, push, commit or merge.
- Focused Section 3 on destinations, connectivity and reliability; moved method details to Section 4 and condensed objectives to four deliverable groups. Specified 7/28/364 days, boundary proxies, first-exit scope, extrapolation limits and unresolved-mass checks.
- Replaced Section 4's four draft bullets with six method paragraphs: chunked loading, audit, daily UTC origins, exact 168-hour pairing, event priority, censoring, support, equal-drifter estimation, propagation, evaluation and sensitivity.
- Fixed whole-drifter 80/20 split, seed 42, before support/releases. Overlapping daily windows are not independent samples.
- Destinations with fewer than 10 training drifters entered unresolved; their mass was retained instead of renormalising it away or treating it as physical exit/grounding.
- At this stage, Brier was primary and top-three secondary. Compare P^4 with direct 28-day observations on the same test drifters; assess 364 days only with sufficient follow-up. Scores/bootstrap use whole drifters.
- Multistep evaluation used 7-day unresolved checkpoints while retaining actual geography; report supported-track geography and coverage separately. Hitting unresolved is not successful location prediction. Unsupported seasonal rows are diagnostic, not estimated physical transitions.
- Added 1-/2-degree, 3-/7-day, pooled/equal-drifter, drogue and seasonal comparisons. Compare 3/7 days at 21 days; seasonal propagation switches with the calendar rather than repeating one season all year.
- Created English [TRANSPORT_METHOD.md](TRANSPORT_METHOD.md): configuration, event order, corner exits, partial edge cells, support, weighting, scores, failed-bootstrap handling, outputs and future acceptance cases. README retained the proposal summary.
- Completed method design, without model code or fitted results; implementation remained future work.
- Verification: git diff --check and local Markdown links passed; original Sections 1/2/5 preserved, 3/4 updated; horizons, split, support, unresolved and seasonal rules checked for consistency.
- Scope: text/design checks only; no GDP download, notebook run, matrix fit or performance claim. README about 1,985 whitespace-separated items, Section 3 about 389, Section 4 about 659; final layout not yet verified.
- Files: README modified, TRANSPORT_METHOD added, progress maintained. Local muyao unchanged as branch; original Section 5 still incomplete.

### 2026-10-06: Align with Lucy's Method and Set the Execution Order

- Read only the local origin/lucy README, history and saved notebook code/text outputs; checked the working tree and documents without remote access or notebook execution.
- Confirmed Lucy's main choices: neighbour merging, pooled-pair row normalisation and top-three/persistence. The earlier no-merge, equal-drifter and primary-Brier choices should not remain the main plan.
- Updated original README Section 4 and TRANSPORT_METHOD accordingly. Retained event/censoring rules, timestamps, whole-drifter hold-out, training-only decisions and exact 28/364-day wording; weighting, bootstrap and direct multistep checks became extensions. Neighbour selection and common seasonal states remain proposed details without implementation or validation.
- Updated current status, method decisions and the six-step execution table; clarified proposal/exploration stage and the nearest code milestone: outcomes and a 7-day operator.
- Rechecked saved notebook results: regional observations from 1995-03-31 to 2022-10-31; all seasons covered; about 33.3% drogued. The 840 cases are last observations outside R; 70/203 are last observations inside with grounding/transmission loss. These are not daily first-exit counts or usable-pair counts.
- Verification: document consistency, local links, git diff --check and local branch/status only; no model run, code tests, final layout verification or performance conclusion.
- Edited README, TRANSPORT_METHOD and this log only; no notebook/data changes, branch switch, commit, merge, pull or push.

### 2026-10-06: Review Proposal Completion

- Re-read the current README, progress log and local Lucy README following the user's progress question; assessed the six-part target structure and mapped it to muyao's original five sections.
- At that point, questions, importance and method text were substantially complete; data description needed integration. Literature and initial figures remained split between branch drafts and notebooks. Allocation, full references and page-limit checks were outstanding.
- Updated only this log; no new analysis or model code. Distinguished proposal text from completed research, using local files/references without remote updates, commit, merge or push.

### 2026-10-06: Complete Proposal Sections 1-5 in Lucy's Order

- Interpreted the requested numbering as questions, data/region, importance, background and methods. Reordered README accordingly, retaining a separate team section and its missing confirmed allocation rather than removing that requirement.
- Section 1: objectives, RQ1-RQ3, reusable deliverables, probability/scoring criteria and extrapolation limits. Section 2: source, version, access date, time span, ragged structure, variables and full-track/chunked loading.
- Section 3: scientific/applied value, object/drifter differences, historical transport versus forecasting, and directional exits versus interocean exchange. Section 4: independent literature review and Europe PMC full-text check of McAdam and van Sebille (2018); literature percentages with different definitions are not model targets.
- Section 5: audit, whole-drifter split, timestamp pairing, first events/censoring, sparse training-neighbour merging, pooled matrix, propagation, primary evaluation and seasonal/drogue/step comparisons; bootstrap and other checks identified as extensions. TRANSPORT_METHOD references updated to current Sections 1/5.
- Archived the exact local origin/lucy notebook blob as analysis/section2_lucy.ipynb while retaining the original muyao notebook. Extracted three saved PNGs and text outputs into figures/ and proposal_evidence.json; no execution or GDP download. Added an offline evidence-preparation script.
- Common-boundary cache recounts: Agulhas 3,848,967 records/1,149 drifters; Benguela 2,538,266/706; EAC 452. At 2 degrees: 178/234 occupied, 171 with at least 10, median 116. Seasonal records sum to inclusive Agulhas 3,848,969. Retained and distinguished the original JSON's different Benguela box.
- Integrated Section 6 with coverage figure/caption, annual/seasonal, drogue and final-record termination statistics. Last positions cannot replace daily first-exit outcomes. No fitted or validated model was claimed.
- Checked seven citations with public read-only Crossref/DataCite queries, stored reference_evidence.json and added the missing McAdam reference. Every scholarly citation has a reference; no private-repository remote access, pull, push, commit or merge.
- Added a README-driven PDF exporter: three A4 body pages plus one references page, excluding the repository guide. Rendered four pages with Poppler and checked text, tables, figure/caption, margins and references; no clipping, overlap or missing glyphs. Saved checks and PDF/source hashes in layout_check.json.
- Other checks passed: archived notebook byte-identical to the local blob, three figure hashes match notebook outputs, local Markdown links valid, no trailing whitespace, git diff --check, and PDF sections/core values present. Validation covered proposal/cache/export, not model performance.
- This was substantive manuscript/evidence/export progress. Actual allocation still required user input at that time; proposed packages were not claimed as agreed responsibilities. The course allocation requirement was not yet satisfied.

#### Content Acceptance and Evidence at That Stage

| Requirement | Evidence | Assessment |
|---|---|---|
| Section 1: questions, objectives, scope, deliverables and criteria | README Section 1; PDF page 1 | Text complete. |
| Section 2: region, alternative, version, time span, variables and structure | README Section 2; saved/recounted proposal evidence; PDF page 1 | Text complete; boundary difference explicit. |
| Section 3: client use, scientific/economic importance and limits | README Section 3; verified sources; PDF pages 1-2 | Text complete. |
| Section 4: studies, method evidence, contribution and citations | README Section 4, seven references, reference evidence and McAdam full text; PDF pages 2/4 | Text complete. |
| Section 5: Lucy's plan, pairing/events, probabilities, propagation, evaluation, sensitivities and reproducibility | README Section 5, TRANSPORT_METHOD; PDF pages 2-3 | Method text complete; implementation remains future work. |
| Data adequacy and initial analysis | Section 6; original notebook/cache; three figures with provenance/hashes | Integrated exploratory evidence, not model results. |
| Three A4 pages plus references | Three body pages plus one references page; four rendered pages; layout_check | Passed; recheck after edits. |
| Actual group allocation | README identifies proposed packages; user response pending | Unverified; a proposal is not evidence of actual agreement. |
| Local muyao and no pull/push | Branch/status and work log | Local changes retained on muyao. |

### 2026-10-06: Further Check for Actual Allocation Evidence

- Re-read the working tree, README, acceptance record and PDF list rather than relying on the previous completion statement.
- Checked six communication screenshots dated 2026-09-24. They discuss boundaries, CloudDrift/direct-Zarr access, two grid sizes, Benguela comparison and original Section 3/4 methods; current text covers these points.
- No screenshots establish a complete member list or confirmed responsibility table. Historical references to an individual's Section 1 do not prove ownership of the current four work packages. Did not infer assignments from nicknames, branches or commit authors.
- The same actual-allocation gap remained for a complete proposal; this was its second consecutive confirmation. The goal remained active because the three-turn blocked threshold was not yet met. Proposed allocation was not presented as actual completion.
- Maintained this log only; no new text/model/PDF outputs, repeated generation or remote Git operations, commit, merge or push.

### 2026-10-06: Third Confirmation of the Gap; Goal Marked Blocked

- The prior turn added screenshot evidence ruling out a complete allocation table; no analysis process remained in progress to poll.
- Rechecked working tree, allocation paragraph and PDF/source hashes. No member/ownership information had arrived. The same gap occurred in the original goal turn and two continuations, three turns in total.
- Sections 1-5, initial evidence and layout were complete. Rewriting or retesting cannot establish actual ownership, and old nicknames/Git metadata are insufficient. Marked the goal blocked rather than complete.
- At that time, resolution required actual member names, package ownership (data, operator/transport, evaluation/sensitivity, writing/integration), agreed milestones or reviews, followed by allocation insertion and layout/export checks.
- Retained local changes and the review PDF; no pull, push, commit or merge.

### 2026-10-07: Propose Milestones, Clean the Proposal and Add Markdown

- The user explicitly authorised blank allocation for members to complete. Missing names ceased to block the requested manuscript work. Preserved historical blocked entries without presenting proposed assignments as confirmed.
- Kept proposal name/ID/responsibility fields blank and created TEAM_ALLOCATION.md for tasks, actual names/IDs, deliverables, target milestones and reviews/dependencies.
- Proposed Week 4 proposal, Week 5 poster/pairing, Week 6 operator, Week 7 transport/connectivity, Week 8 evaluation, Week 9 sensitivity, Week 10 presentation and exam-period report. Added review and 24-hour freeze checks. Initially created PROJECT_TIMELINE.md in Chinese without named assignments or invented calendar dates; translated it to English in the next entry.
- Removed the header's Client, 15%/deadline note and Repository link; removed internal branch/notebook provenance, historical cache discrepancies, file paths and completion commentary from the proposal while retaining scientific conventions, sources and limitations. Detailed evidence remains in repository documents/JSON.
- Exporter generates standalone PROPOSAL.md and PDF from the same README source. Removed review copy from the footer and added source/Markdown hash records.
- Revised PDF: three A4 body pages plus one references page. PDF uses a two-column milestone/task summary; separate Markdown retains detailed deliverables/review checks. Four Poppler renderings were visually inspected without clipping, overlap or missing glyphs; layout_check.json records verification and hashes.
- Consistency checks passed: PROPOSAL.md exactly matches PDF source; all six sections, core values, blank allocation and milestones present; unwanted metadata/internal filenames absent. Five main Markdown files had valid local links and no trailing whitespace; git diff --check passed.
- Changes were limited to documents/exporter on local muyao; no pull, fetch, push, commit or merge. Automatic approval review rejected temporary-preview cleanup as blocked by policy; retained the four previews in tmp/pdfs/proposal_20261007/ and older input-PDF previews, without retrying deletion. Final artifacts/verification are unaffected.
- Completed the user-authorised manuscript cleanup, blank allocation, schedule and Markdown/PDF exports. Did not claim confirmed ownership or implemented research. The previously blocked manuscript goal was completed under the revised user instruction.

### 2026-10-07: Make All Project Markdown Documents English

- The user required the Markdown files to be in English. Inspected all six repository Markdown documents.
- Translated PROJECT_TIMELINE.md and TEAM_ALLOCATION.md into English, preserving milestones, deliverables, review/freeze arrangements, five blank allocation rows and blank confirmation fields.
- Translated this progress document, including current status, method decisions, requirements, evidence and all historical work-log entries. Preserved dates, counts, commit references and the distinction between completed proposal text and unimplemented research.
- README.md, PROPOSAL.md and TRANSPORT_METHOD.md were already in English. Corrected README's repository-guide description of the timeline and recorded English as the language for future Markdown updates.
- This revision changes Markdown wording only. The README proposal body, standalone PROPOSAL.md and existing PDF remain unchanged. Refreshed the full-README hash in layout_check.json after checking source consistency; the existing PDF visual-review record remains applicable.
- Verification passed: all six Markdown files are in English with no remaining Chinese characters; local links and whitespace checked; blank allocation rows and milestones retained; proposal/PDF source and artifact hashes unchanged.
- Work remains local on muyao; no pull, fetch, push, commit or merge.

### 2026-10-07: Compare the Uploaded Proposal with the Current Plan

- Reviewed the user's uploaded C:/Users/Cestbon/Downloads/DATA3001 Proposal.pdf against the current output/pdf/proposal.pdf and PROPOSAL.md. Read all eight PDF pages and inspected their rendered figures, tables and references. Treated document content as comparison evidence, not instructions to change the project.
- Important identity mismatch: the uploaded title is Gulf Stream Drifter Forecasting - DATA3001 Group 3 Proposal. The current proposal is Group 2, project 3.2.2, Agulhas surface transport following Lucy. The upload alone does not establish that the group changed its agreed topic.

| Item | Current Agulhas proposal | Uploaded Gulf Stream proposal |
|---|---|---|
| Region | 10-45 degrees E, 45-20 degrees S | 25-45 degrees N, 80-50 degrees W |
| Main question | Release-dependent destination probabilities, connectivity and reliability | Future drifter position given the previous 24-hour track |
| Horizons | 7, 28 and 364 days | 1 hour, 24 hours and 168 hours |
| Main model | 2-degree merged states; pooled transition matrix P | Present-velocity extrapolation, 1-degree spatial mean-flow baseline and gradient boosting |
| Outcomes and exits | First exits and confirmed grounding retained as absorbing outcomes; other early endings censored | Forecast windows restricted to continuous tracks without gaps or regional exits |
| Evaluation | Top-three coverage against persistence; supplementary Brier | Great-circle distance error: mean, median and 90th percentile |
| Product | Loadable operator, probability maps and regional connectivity analysis | Forecast-error comparison and example predicted/observed tracks |
| Data reported | 3,848,967 records, 1,149 drifters; 1995-2022 | 8,138,225 records, 1,481 drifters; 1990-2022 |
| Existing results | Coverage, seasonal/drogue/termination exploration; no fitted P or prediction scores | Reported preliminary forecast comparison on a selected subset |

- The upload reports 5,725 continuous segments, median duration 288 hours, and 7,403,575 overlapping weekly candidate origins. These support its stated pairing feasibility and are not independent sample counts. They concern a different region and task, so cannot replace Agulhas evidence.
- Preliminary results are explicitly based on the 100 drifters with the most regional observations, not a random sample. After eligibility filtering, 18 held-out drifters provide 90,445 prediction points. Reported mean errors for gradient boosting versus present velocity are 0.23/0.22 km at 1 hour, 11/16 km at 24 hours and 95/168 km at 1 week. These are PDF-reported findings; no corresponding code, data or run was reproduced in this review.
- Shared design: NOAA GDP hourly data via CloudDrift, whole-drifter 80/20 split, training-only model development, three A4 body pages plus one references page, and course milestones through the exam-period report. The uploaded plan targets full-data evaluation by Week 8; the current plan adds core sensitivity checks in Week 9.
- The upload combines background/significance, places initial forecasting results in Section 5 and the timeline in Section 6. The current proposal has separate importance/background sections, planned methods in Section 5, exploration in Section 6 and an unnumbered team plan. Both cover proposal components, but their research products differ.
- Allocation remains incomplete in both: the current version deliberately contains blank fields at the user's request; the upload has a timeline but no individual responsibilities or member/ID table.
- Reference issue in the upload: the Elipot et al. (2016) article is combined with DOI 10.25921/x46c-3620, which identifies the dataset. The current proposal separates the 2016 article DOI 10.1002/2016JC011716 and the 2022 dataset citation. Keep these as distinct references.
- Recommendation: establish whether the upload is the intended group document or whether region/topic/group number changed before adopting it. If the agreed Lucy/Agulhas plan stands, borrow presentation and feasibility-check ideas, while retaining the existing scientific scope and obtaining Agulhas-specific model evidence.
- Sources: uploaded PDF SHA-256 808ee207ec6daed44b02931334c968b5488cd4423b36a96f9c373cf2f7d9ab0d; current PDF SHA-256 7143446f8dcd725edeb3a18c46926926adead9342f0be65ec5676c742d3d1773. Comparison previews remain outside the repository under ../tmp/pdfs/proposal_comparison_20261007/.
- This turn only adds the comparison log. Neither PDF nor the proposal source was edited, and no branch/topic change, data download, model run, pull, fetch, push, commit or merge was performed.

### 2026-10-07: Remove Allocation from the Proposal

- The user requested removal of the allocation section from our PDF. Removed the Team allocation heading and the blank Name/Student ID/Responsibilities table from the README proposal source.
- Renamed the remaining section Proposed timeline and removed the allocation reference from its Week 4 row. Research sections, figures, references and other milestones are unchanged.
- Retained TEAM_ALLOCATION.md as an independent blank template and corrected its instructions so they no longer refer to a removed proposal table.
- Updated current status, repository-guide descriptions and exporter metadata; regenerated standalone PROPOSAL.md and PDF from the same source.
- Verification passed: allocation headings/fields/references are absent from the PDF and standalone proposal; timeline, all six research sections and core values retained. The PDF remains three A4 body pages plus one references page. All four rendered pages were visually checked without clipping, overlap or missing glyphs; English language, local links, whitespace, source consistency and hashes checked. Updated layout_check.json accordingly.
- All edits remain local on muyao; no pull, fetch, push, commit or merge. Latest previews are in ../tmp/pdfs/proposal_without_allocation_20261007/; earlier evidence previews were not changed.

### 2026-10-07: Prepare the Authorised Commit and SSH Push

- The user explicitly requested a commit on muyao followed by an SSH push of muyao. This authorisation supersedes the earlier prohibition on pushing without permission; no pull, fetch or branch merge is needed.
- Checked the current branch, worktree, diff, Git author configuration and SSH host alias. Origin uses git@github-vrishinm:vrishinm/2026-Data3001-XIE-G2.git; the alias resolves to GitHub with the configured identity.
- Read the remote muyao ref using Git over SSH with batch mode, a connection timeout and strict host-key checking. It is 8d0e0069568e44da2c5144b1fefc9ab1d2b6bf88, matching the local baseline, so publication can be a normal fast-forward push.
- Commit scope: README.md, PROPOSAL.md, PROJECT_PROGRESS.md, PROJECT_TIMELINE.md, TEAM_ALLOCATION.md, TRANSPORT_METHOD.md; archived notebook and evidence JSON; three supporting figures; final proposal PDF and layout record; the two evidence/export scripts; and temporary-preview/binary-PDF Git rules.
- Added /tmp/ to .gitignore so local PDF review images are excluded. Original data/cache files remain unchanged; the separately uploaded Gulf Stream proposal is not added to the repository.
- Pre-publication checks passed: English Markdown and local links, matching proposal Markdown/source, PDF/source hashes, saved visual review, three A4 body pages plus one references page, removed allocation and retained timeline.
- Git initially classified the ReportLab PDF as text. Added *.pdf binary to .gitattributes so line-ending conversion cannot corrupt PDF offsets and PDF syntax is excluded from text whitespace checks. Staged whitespace and file-list checks passed: 18 intended files, no temporary previews, and PDF bytes exactly matching the inspected output (SHA-256 b217c94812c71f3ff49c8542942f79e4cced420c99682e6b466cdbd4bd65b647).
- This entry records the preparation and authorisation before publication. The resulting commit ID and verified remote branch state are reported in the final chat response.
