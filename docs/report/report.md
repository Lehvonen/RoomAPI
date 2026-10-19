# An Experience Report on a Specification-Driven, AI-Assisted Software Construction Project

## Team Details (Team TODO: team number/name)

| Student Name | Student ID | Role in the project | Contribution (%) |
|---|---|---|---|
| Ivar Lehvonen | 2202699 | Prompt Engineer | TODO |
| Kristoffer Elfving-Millan | 2201244 | Code Auditor | TODO |

## Executive Summary

<!-- 200–300 words. Must clearly state:
1. The system built
2. The specific formal/semi-formal specification techniques used
3. The AI models/tools leveraged
4. The SDD workflow used in the project
5. The SDD tool used (Spec Kit)
6. The verification and validation method used to ensure the AI-generated code implements the specifications -->

## 1. Introduction & Paradigm Shift (3 Points)

### 1.1 Project Overview & Objectives

<!-- Overview of the project and the solution intended to be built. -->

### 1.2 The Vibe Coding

<!-- What vibe coding is and how the team approached development using vibe coding. -->

### 1.3 The SDD Methodology

<!-- Introduce SDD and how the team approached it. Which tool was used and why.
Project specifications and scope, summary of the development timeline,
optionally the workflow of the project (both vibe coding and SDD). -->

## 2. Requirements & System Specification (6 points)

<!-- The "source of truth" constructed to feed into the AI. Most critical section. -->

### 2.1 Stakeholders

<!-- The stakeholders and why they were chosen. -->

### 2.2 Functional Requirements

<!-- What functional requirements are, then this project's functional requirements. -->

### 2.3 Non-Functional Requirements

<!-- What non-functional requirements are, then this project's (performance, security, usability, reliability constraints). -->

### 2.4 Technology Stack

<!-- The stack and the reasons for choosing it. -->

AI Generation & Orchestration Tools: TODO

### 2.5 Interface & API Specifications

<!-- The API the system exposes: endpoints, methods, who may call them, request and response schemas, status codes.
The exported OpenAPI spec goes in docs/. -->

### 2.6 How these requirements and specifications were created (using SDD AI tools)

<!-- How the SDD AI tools (Spec Kit + coding agent) were used to produce the requirements and specifications above. -->

## 3. Vibe coding and your project (5 pts)

<!-- The approach, and how it was decided among team members: any promptbook,
how the project was divided into modules and how they were combined. -->

### 3.1 Prompting Framework

<!-- Prompting techniques used: chain-of-thought, automated agentic workflows, ... -->

### 3.2 Master Prompts / System Prompts

<!-- Per significant prompt (source: docs/vibe/prompt-log.md): original text, purpose, reasoning,
expected output, evaluation, issues, refinement and why, how the revision improved the outcome.
Include representative prompt-response examples and reflect on the importance of prompt engineering. -->

### 3.3 Prompt Iteration Log

<!-- An example where a prompt failed or hallucinated, and how the prompt or specification was refined (source: docs/vibe/prompt-log.md §3.3).
"What did not happen according to your plan": which task was not done.
"Modified Prompt": how you modified the prompt, and the modified prompt. -->

| Initial Prompt/Specification | AI Failure Mode / Bug Produced | Refined Prompt/Specification | Resulting Code Quality | What did not happen according to your plan | Modified Prompt |
|---|---|---|---|---|---|
| | | | | | |

## 4. Specification Driven Development and Your Project (7 pts)

### 4.1 SDD Tool-kit

<!-- The toolkit (Spec Kit) and the reason for choosing it. -->

### 4.2 Development Environment

<!-- System environment and IDE/coding agents used, and why. -->

### 4.3 Deriving the requirements using the IDE/coding agents

<!-- How FRs and NFRs were derived with the toolkit and IDE, including the prompts. Possible activities:
SRS, system constraints, interfaces, acceptance criteria, compliance requirements. -->

### 4.4 SDD Workflow and Implementation

<!-- Which workflow was used. Any existing workflow can be adopted, or propose the team's own. -->

### 4.5 Prompts

<!-- Same as 3.2, for SDD (source: docs/sdd/prompt-log.md). -->

## 5. Verification and Validation (6 pts)

### 5.1 V&V Strategy

<!-- How the code was verified (TDD with AI and/or human-in-the-loop), including threats to validity.
Possible activities: unit, integration, functional testing, requirement verification, UAT, compliance testing. -->

### 5.2 Code Audit Log

<!-- Security, compliance and logical flaws caught in review; whether AI or AI+human found and fixed them; the technique used. -->

| Issue Found | Type (security / compliance / logic) | Found by (AI / AI+human) | Resolution |
|---|---|---|---|
| | | | |

### 5.3 Test Execution Results

<!-- Per test: expected result, actual result, pass/fail. Evidence (screenshots, console output, logs) in docs/evidence/.
Defects and how they were resolved or why not. Metrics: executed, passed, failed, coverage. -->

| Test | Expected | Actual | Pass/Fail |
|---|---|---|---|
| | | | |

## 6. Project Management & AI Toolchain Workflows (3 points)

### 6.1 Version Control & Prompt Integration

Git Commit Conventions:

We set up the conventions at the start of the project, before writing any code, so that the Git history would be easy to follow for both us and the course staff.
Every commit message says what kind of change it is and what it belongs to, a requirement, a prompt round or a report section, so a commit can be traced back to the spec or the report.
Not every rule was followed exactly. Most of the commits are on Ivar's account, which is explained in 6.2.

From CONTRIBUTING.md:

Format: `type(ref): description`

- `ref` is a spec ID (`FR-04`, `NFR-02`), a prompt round (`round-3`),
  a report section (`report-s5`), or `report` for a change spanning several sections
- types: feat, fix, test, docs, spec, vibe, chore

Examples:
- `vibe(round-3): add login endpoint`
- `feat(FR-04): reject overlapping bookings`
- `test(FR-04): overlap edge cases`
- `docs(report-s2): non-functional requirements`

Workflow:

- Every change goes through a pull request; no direct pushes to main
- Every PR links an issue (`Closes #12`)
- Every feature and every report section has its own issue, assigned to one member
- Discuss decisions in the issue or PR, not only in chat, so they are visible in Git
- Commit from your own GitHub account; every member opens, reviews and merges their own share of PRs
- Log every prompt in `docs/vibe/prompt-log.md` or `docs/sdd/prompt-log.md`, in the same PR as the code it produced
- Never edit `vibe/` after it is marked frozen

Every prompt we gave the AI was saved in a prompt log, docs\vibe\prompt-log.md for the vibe version and docs\sdd\prompt-log.md for the SDD version.
The prompt was committed in the same pull request as the code it produced, so the prompt and its result can always be found together.
Each log entry also says who wrote the prompt (the actuall thinking and desicion was done as a group), which model was used, what we expected and what came back.
Some prompts were drafted by the AI and then read and approved by us, and that is written in the log as well.
For the SDD version, Spec Kit split the work into six task groups (A–F).
Every group got its own issue and its own pull request (issues #16–#21, pull requests #23–#28), and commits use the requirement ID they implement, like feat(FR-013).

Workspace Configuration:

| What | Where |
|---|---|
| Claude Code, `claude-opus-5-5` | docs\vibe\prompt-log.md, docs\sdd\prompt-log.md |
| Spec Kit 1.1.4.dev0, installed as Claude Code skills: speckit-analyze, speckit-checklist, speckit-clarify, speckit-constitution, speckit-converge, speckit-implement, speckit-plan, speckit-specify, speckit-tasks, speckit-taskstoissues | sdd\.claude\skills\ |
| uv, Python 3.11 or newer | sdd\pyproject.toml, sdd\uv.lock |
| GitHub Actions workflow `sdd-tests`: on every pull request and every push to main, runs `uv sync --locked` and `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80` in `sdd/` on Python 3.12 | .github\workflows\sdd-tests.yml |
| Pull request template (What, Spec / prompt reference, Verification, Closes #) and a Task issue template | .github\pull_request_template.md, .github\ISSUE_TEMPLATE\task.md |
| Branch protection on `main`: changes through a pull request, 1 approving review required | GitHub repository settings |

Claude Code was the only AI tool we used, and it ran on Ivar's computer and account. Spec Kit was installed into Claude Code as skills, so the SDD steps could be run as commands straight from Claude Code.
We worked together over Discord with screen sharing on, so both of us saw every prompt and every answer as it happened.
The GitHub Actions workflow ran the tests on every pull request, so a pull request with failing tests or under 80% coverage could not be missed when reviewing.

### 6.2 Team Contribution Breakdown

In a normal project most of the time would go into writing code. In this project we did not write the code ourselves, the AI did it.
Instead our time went into deciding what the system should do, writing and approving prompts, and checking what the AI produced.
Ivar's role as Prompt Engineer was to run the prompts and the Spec Kit steps. Kristoffer's role as Code Auditor was to review the pull requests and check that the code matched the spec.
The biggest shift was in the SDD version, where the clarify step made us make the decisions that the AI had made by itself in the vibe version. We went from writing code to specifying, reviewing and orchestrating the AI.

From section 3:

The Git history shows Ivar as the author for all of the code and prompt commits. This is because Ivar was the only person that had access to Claude Code, so every prompt had to run trough his account. 
Instead of "faking" the Git history by loging in on Kristofers GitHub account on Ivars computer to achive a 50/50 commit split on the coding we decided to not try and deceive anyone and instead mention it in the report.
The work itself was done together. Every step, from reading/writing the prompts to reading the output and probing the API, was done over Discord while screen sharing on, and all of the decisions were made by both of us.
Kristoffers part as the Code Auditor shows up in Git history and merges, all though we both shared that work aswell, we split the workload 50/50 and did not read the same files (except for when we did by accident).
We decided at PR #22 that maybe we should have Kristoffer merge the PRs just so that he wouldnt be 100% excluded from the Git history in the coding part of the project.

Git activity on GitHub as of 2026-10-19:

| | Ivar (@Lehvonen) | Kristoffer (@iPonkko) |
|---|---|---|
| Commits | 89 | 9 (all merge commits) |
| Pull requests opened | 16 | 0 |
| Pull requests merged | 3 | 9 |
| Pull request reviews | 0 | 11 |
| Issues assigned | 14 | 4 |

<!-- TODO (us): update the table before submitting, once Kristoffer's sections (#5, #7, #8, #10) are merged. -->

## 7. Reflections on Specification-Driven Development (5 points)

### 7.1 Benefits of AI-Assisted SDD

### 7.2 Core Bottlenecks and Challenges

### 7.3 Lessons Learned & Best Practices

<!-- Critical evaluation backed by concrete examples; evidence-based vibe coding vs SDD comparison;
successes and limitations; actionable best practices; balanced conclusion. -->

<!-- Evidence to quote in the vibe-vs-SDD comparison: in vibe round 2 the agent changed API responses
from UTC (Z) to local time (+03:00) without being asked, a contract change nobody agreed to
(docs/evidence/vibe-round-2/findings.md, "What round 2 decided on its own"). -->

### 7.4 Proposed Specification-Driven Development Workflow

<!-- A reusable workflow: each phase's objectives, activities, inputs, outputs and deliverables;
where AI/vibe coding fits and where human oversight is essential; justification from project evidence;
a process diagram. -->
