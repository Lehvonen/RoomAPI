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

The idea was to build the same system twice, once by vibe coding and once with Specification-Driven Development (SDD), and then compare the two.

The system we chose is RoomAPI, a REST API for booking meeting/study rooms.
Users can register, log in, see the list of rooms, check when a room is free, book it, and see and cancel their own bookings.
Admins can create, edit and deactivate rooms and cancel any booking.
The most important rule is that two bookings for the same room can never overlap.

We kept the scope to the API only, so there is no front end and nothing is hosted. Both versions are written in Python with FastAPI and SQLite.

Our objectives were to get a working API out of both methods, to keep the comparison fair by giving both versions the same features and running the same tests on both, and to be able to trace every requirement to a test.
We also wanted every prompt logged in Git, so that anyone can see what the AI was asked and what it produced (docs\sdd\prompt-log.md, docs\vibe\prompt-log.md).


### 1.2 The Vibe Coding

Our approach to the vibecoded version was to atleast try to have the same functional features as we would have in the SSD version so that they could be compared to each other.
We used Claude Code with Opus 5.5 on medium effort, working only in vibe/.

#### Round 1
The first promt was written by us. The prompt was a short feature list with no rules or limits, except for the vibe/ constraint. We wanted to show and also see for our self the choices that the AI would make. 
After that we probed the API and found 4 bugs and 5 rules the agent had chosen without asking.

#### Round 2
The problems were described as plain symptoms, without saying how to fix them. We decided to have another agent write the prompts to a fresh agent that we read and approved.
No AI generated promt was edited for the vibe version, because we wanted to see how capable the AI realy was. In retrospect it would have been interesting to experiment with different models and effort levels.

After Round 2 we frozze vibe/ at b68a979 to serve as the baseline. The full prompts, outputs and iteration log are in the vibe prompt log (docs\vibe\prompt-log.md).

### 1.3 The SDD Methodology

#### Tool

For the SDD version we used GitHub Spec Kit together with Claude Code, with the same model and effort level as the vibe version, Opus 5.5 on medium effort.
Spec Kit was the tool named for the course, and it works directly inside Claude Code, which we were already using.
Keeping the same agent and model also made the comparison fairer, since the only thing that changed was the method.

#### Approach

We started by writing a constitution with five principles: Specification First, Test-First, Secure by Default, Explicit Time Handling and Simplicity (sdd.specify\memory\constitution.md).
After that we followed the Spec Kit steps: specify, clarify, plan, tasks and implement.
The clarify step was the biggest difference to the vibe version. This time we decided the rules ourselves instead of letting the AI pick them. For example, bookings are only allowed 08:00–18:00, at most 4 hours long, and can't be edited.
The specification ended up with 17 functional and 9 non-functional requirements, which are described in section 2 (sdd\specs\001-room-booking-api\spec.md).

#### Timeline

On 13 October we set up the repository and ran the first vibe round.
On 16 October we probed the vibe API, ran round 2 and froze it. The same day we wrote the whole SDD specification, from constitution to tasks, and implemented the 37 tasks in six pull requests.
The specification itself took around ten minutes, which surprised us. In retrospect we should have spent more time reading what the AI produced before moving on to the next step.
This fast timeline was requiered due to group members different schedules and time left over from work and other courses.

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
