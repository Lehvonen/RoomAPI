# An Experience Report on a Specification-Driven, AI-Assisted Software Construction Project

## Team Details

| Student Name | Student ID | Role in the project | Contribution (%) |
|---|---|---|---|
| Ivar Lehvonen | 2202699 | Prompt Engineer | 50% |
| Kristoffer Elfving-Millan | 2201244 | Code Auditor | 50% |

## Executive Summary

Our system is a RoomAPI, a REST API for booking meeting/study rooms like what we have in Aurum, although we do not have any rooms to actually book.
We buit the API twice, first version was a fully vibecoded version where even the AI wrote the prompts, we wanted to fully embody the vibe coding aspect.
The second version was done with Specification-Driven Development (SDD).

For the SDD version we used GitHub Spec Kit together with Claude Code, and the AI model behind both versions was Claude Opus 5.5 on medium effort.
Spec Kit gave us a fixed workflow to follow: constitution, specify, clarify, plan, tasks and implement.
The specification was written as user stories with Given/When/Then acceptance scenarios, 17 numbered functional requirements, 9 non-functional requirements, a data model and an API contract.
The clarify step was where we actually had to make decisions, things like how far ahead you can book and what happens after too many failed logins.
The implementation was then split into 37 tasks, which we merged in six pull requests.

To check that the AI-generated code really does what the spec says, every requirement is mapped to at least one test in a traceability matrix.
The SDD version passes all 186 tests with 94.8% code coverage, and we also broke the code on purpose in two places to make sure the tests notice it.
Finally we ran the same tests against both versions. The SDD version passed 155 out of 155 and the vibe version 114 (out of the 166 tests only 155 of them could run over HTTP against both, the other 11 need the test database witch the vibecoded version does not have).
None of the vibe version's failures were crashes; it simply made its own choices where our spec had decided something else.


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

Workspace Configuration:

### 6.2 Team Contribution Breakdown

<!-- How roles shifted from coding to specifying, prompting, auditing and orchestrating. -->

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
