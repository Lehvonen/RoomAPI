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

The Git history shows Ivar as the author for all of the code and prompt commits. This is because Ivar was the only person that had access to Claude Code, so every prompt had to run trough his account. 
Instead of "faking" the Git history by loging in on Kristofers GitHub account on Ivars computer to achive a 50/50 commit split on the coding we decided to not try and deceive anyone and instead mention it in the report.
The work itself was done together. Every step, from reading/writing the prompts to reading the output and probing the API, was done over Discord while screen sharing on, and all of the decisions were made by both of us.
Kristoffers part as the Code Auditor shows up in Git history and merges, all though we both shared that work aswell, we split the workload 50/50 and did not read the same files (except for when we did by accident).
We decided at PR #22 that maybe we should have Kristoffer merge the PRs just so that he wouldnt be 100% excluded from the Git history in the coding part of the project.

### 3.1 Prompting Framework

We didnt use any specific prompting technique like chain-of-thought or few-shot examples, and we didnt give the AI a system prompt or a role. This was done on purpose.
Claude Code is an agentic tool, so a single prompt was enough to build the whole API. The agent planned the work, wrote the files, installed the packages, wrote its own tests and ran them without us asking it to.

#### Round 1
The first prompt was zero-shot, a plain feature list in normal language. The only things we added were a boundary (only read and write filles inside vibe/) and asking it to tell us how to run it.

#### Round 2
The second prompt was written like a bug report. Every problem was one bullet describing the symptom, not how to fix it. 
Where a rule was missing, the prompt only said that there should be one ("There should be a max booking length and opening hours"), so the agent had to choose the limits itself.
The prompt was drafted by the Claude Code session that had probed the API, and then sent to a fresh agent that had not seen anything else. That way the agent only knew what the prompt told it, like a developer getting a bug report from a tester.
We also added "do not run any git commands" so that we had time to actually read the output and commit/push when we decided to.

### 3.2 Master Prompts / System Prompts

#### Round 1

| Field | Entry |
|---|---|
| Date | 2026-10-13 |
| Who prompted | Ivar Lehvonen |
| Tool / model | Claude Code, Opus 5.5 |
| Commit | `75113b5` |
| Raw output | [`round-1-output.md`](../vibe/round-1-output.md) (terminal paste, not verbatim; see the note at its top) |
| Purpose | Get a working baseline API for the vibe-vs-SDD comparison, with no spec. |
| Reasoning for the wording | Plain feature list, the way a developer would describe it, deliberately without rules or restrictions, so the agent's own choices show. |
| Expected result | A somewhat runnable API covering partially the features, with gaps in edge cases |
| What came back | FastAPI + SQLite API in `vibe/`: register/login with JWT, list rooms, room availability, create/list/cancel bookings, admins create and edit rooms and cancel any booking, admin created via a CLI command. The agent wrote 21 tests and reported all passing. |
| Choices the agent made without being asked | Times without a timezone treated as UTC; no booking in the past; regular users can't cancel an ended booking; cancelled bookings kept with status `cancelled`; random JWT key if `ROOMAPI_SECRET_KEY` is unset. |
| Met expectations? | It ran and covered all of the features, but missed limits that wasnt specified |
| Issues (incorrect, incomplete or inefficient code) | Found afterwards by probing; none was caught by the agent's own 21 tests. 4 real bugs: 3 inputs cause an unhandled error (HTTP 500), and deactivating a room leaves its bookings active. 5 rules the prompt never specified, where the agent picked a default without asking. See §3.3 and [`docs/evidence/vibe-round-1/findings.md`](../evidence/vibe-round-1/findings.md). |
| Refinement and why | Round 2: the probe failures were turned into a loose list of symptoms, without saying how to fix them (see Round 2). |

Prompt (verbatim):

```text
Build a room booking REST API in Python with FastAPI and SQLite.

Users should be able to register and log in. Logged-in users can see a list of rooms, check when a room is available, book a room for a time slot, see their own bookings and cancel them. There should also be admin users who can create and edit rooms and cancel any booking.

Only read and write files inside the vibe/ folder. Do not touch anything outside it. Tell me how to run it.
```

#### Round 2

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | Claude Code, on behalf of Ivar Lehvonen, who delegated round 2. The prompt was written by the Claude Code session that ran the round-1 probe, and sent to a fresh agent that saw nothing else. Prompt and reasoning approved by Ivar Lehvonen on 2026-10-16: AI-drafted, human-approved. |
| Tool / model | Claude Code agent with fresh context (`claude-opus-5-5`) |
| Commit | `b68a979` |
| Raw output | [`round-2-output.md`](../vibe/round-2-output.md) (verbatim) |
| Purpose | Fix the 9 failures the round-1 probe found ([findings](../evidence/vibe-round-1/findings.md)). |
| Reasoning for the wording | Written the way a vibe coder reports bugs: the symptoms in plain words, one bullet per problem, with no limits, rules or design given. Where a rule was missing, the prompt only says one should exist ("There should be a max booking length and opening hours"), so the agent has to choose. The boundary sentence from round 1 is kept, plus "do not run any git commands" so commits stay with the team. |
| Expected result | All 6 symptoms fixed, with the agent choosing its own limits; existing behaviour unchanged. |
| What came back | All 6 fixed in `vibe/` only; 12 new tests, 33 in total, all passing. New settings module `app/config.py`, new dependency `tzdata`. Re-probe: the 9 round-1 failures now pass and the 5 checks that held still hold ([findings](../evidence/vibe-round-2/findings.md)). |
| Choices the agent made without being asked | Maximum booking 8 hours; bookings only 07:00–20:00 local time within one day; time zone `Europe/Helsinki`, with responses switched from UTC to local time with an offset; passwords at least 10 characters with letters plus a digit or symbol, 5 distinct characters, not the username, not a common password; lockout after 5 failures per username or 20 per IP in 15 minutes (429); deactivating a room cancels its upcoming bookings, and so does every startup, for rooms that were already inactive. |
| Met expectations? | Partly. Every symptom is fixed, but the lockout created new problems (N1, N1b), and the switch from UTC to local-time responses changes the API's output format. |
| Issues (incorrect, incomplete or inefficient code) | N1: anyone can lock a real user out for 15 minutes with 5 wrong passwords; the agent flagged this itself. N1b: 20 failures from one IP with any usernames lock out everyone behind that address (campus NAT, proxy). R1: the lockout check isn't atomic, so parallel requests get extra guesses. R2: the startup cleanup cancels bookings without recording who cancelled them. Bookings stored as UTC before round 2 are not corrected. See [findings](../evidence/vibe-round-2/findings.md). |
| Refinement and why | None. The vibe version is frozen after round 2 so it stays a baseline for the SDD comparison; N1 is kept as evidence. |

Prompt (verbatim):

```text
I tested the room booking API in vibe/ and found some problems:

- really big ids (like 2^70) in the url or in a booking give a 500 error
- a booking with a date at the very end of year 9999 also gives a 500
- if an admin deactivates a room, the bookings for that room stay active
- you can book a room for 10 years, or in the middle of the night. There should be a max booking length and opening hours
- we are in Finland. Times without a timezone get saved as UTC, so they end up 3 hours wrong
- passwords like aaaaaaaa are allowed, and you can try wrong passwords forever

Fix these. Only read and write files inside the vibe/ folder (C:\Users\lehvo\RoomAPI\vibe). Do not touch anything outside it, and do not run any git commands. Tell me what you changed and how to run it.
```

#### How the revision improved the outcome
Round 2 fixed everything we asked for. When we ran the same probe again, all 9 failures from round 1 passed, and the 5 checks that already worked still worked.
But the fixes also brought new problems. The login lockout means anyone can lock a real user out for 15 minutes with 5 wrong passwords (N1), and 20 failed logins from one IP address lock out everyone behind it (N1b). The agent also changed the API to return local time instead of UTC, which we never asked for.
So the code got better at what we pointed out, but every rule we left open was decided by the AI, and not always in a way we would have chosen.

#### Example response

Round 2, point 6 of the agent's final reply, verbatim (docs\vibe\round-2-output.md):

> 6. **Passwords and login attempts:**
>    - **New passwords** must be at least 10 characters, include letters plus a digit or symbol, use at least 5 different characters, not contain the username, and not be on a short list of common passwords. The same rules apply to `create-admin`. Existing passwords keep working.
>    - **Login lock:** 5 failed logins for one username, or 20 from one IP address, within 15 minutes lock further attempts with a 429 error that says how long to wait. A successful login resets that username's count.
>    - Locking a username also means anyone can lock a real user out for 15 minutes by guessing wrong on purpose. If the API runs behind a proxy, every request looks like it comes from the same IP, so the per-IP limit would apply to everyone together.

#### Reflection

The biggest thing we learned from the vibe version is that everything the prompt does not say, the AI decides by itself.
In round 1 we never mentioned opening hours, booking length or time zones, so the agent picked its own defaults, and its own 21 tests did not catch any of the problems we later found.
In round 2 we described the problems as symptoms, and the agent fixed them, but it also chose the rules itself, like the 8 hour limit and the lockout. Some of those choices were worse than the bugs they fixed.
To get the result we actually wanted, the prompt would have needed the decisions made beforehand: what the limits are, how logins should be protected and what format times are returned in. At that point the prompt starts to look like a specification, which is exactly what we did in the SDD version.

### 3.3 Prompt Iteration Log

| Initial Prompt/Specification | AI Failure Mode / Bug Produced | Refined Prompt/Specification | Resulting Code Quality | What did not happen according to your plan | Modified Prompt |
|---|---|---|---|---|---|
| Round 1 prompt (§3.2) | Bug: huge IDs (2^70) in a path or body cause an unhandled error, HTTP 500 (probe P4a, P4b) | "really big ids (like 2^70) in the url or in a booking give a 500 error" | Fixed: IDs limited to 1…2^63−1, now 422 | Nothing: fixed as asked | Round 2 (§3.2): the failure described as a symptom, no fix specified |
| Round 1 prompt (§3.2) | Bug: a booking near year 9999 overflows during the UTC conversion and causes an unhandled error, HTTP 500 (probe P5) | "a booking with a date at the very end of year 9999 also gives a 500" | Fixed: out-of-range dates now 422 | Nothing: fixed as asked | Round 2 (§3.2): the failure described as a symptom |
| Round 1 prompt (§3.2) | Bug: deactivating a room leaves its future bookings active, while the owner can no longer see the room (probe P3) | "if an admin deactivates a room, the bookings for that room stay active" | Fixed: deactivation cancels upcoming bookings in the same step | The agent also chose, unasked, to cancel bookings in already-inactive rooms at every startup | Round 2 (§3.2): the failure described as a symptom |
| Round 1 prompt (§3.2) | Unspecified in the prompt → agent chose no maximum booking length and no opening hours: one user can book a room for 10 years, or at 03:00 (probe P1, P2) | "you can book a room for 10 years, or in the middle of the night. There should be a max booking length and opening hours" | Fixed, with limits the agent chose itself: at most 8 hours, 07:00–20:00 local time | The limits were never agreed by the team; the agent chose them | Round 2 (§3.2): said a rule should exist, without saying what it is |
| Round 1 prompt (§3.2) | Unspecified in the prompt → agent chose to read times without an offset as UTC, so Helsinki summer times (UTC+3) are stored 3 hours off (probe P6) | "we are in Finland. Times without a timezone get saved as UTC, so they end up 3 hours wrong" | Fixed: naive times read as `Europe/Helsinki` | Responses changed from UTC to local time with an offset, an unrequested API format change; bookings stored before round 2 are not corrected | Round 2 (§3.2): the failure described as a symptom, with the location |
| Round 1 prompt (§3.2) | Unspecified in the prompt → agent chose length ≥ 8 as the only password rule and no limit on failed logins (probe P7, P8) | "passwords like aaaaaaaa are allowed, and you can try wrong passwords forever" | Fixed: stronger password rules; lockout after 5 failures (429) | New problems: anyone can lock a real user out for 15 minutes (N1), and 20 failures from one IP lock out everyone behind it (N1b); not fixed, vibe frozen | Round 2 (§3.2): the failure described as a symptom |

(docs\vibe\prompt-log.md).

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
