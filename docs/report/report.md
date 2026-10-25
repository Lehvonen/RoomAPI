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

We used GitHub's Spec Kit (version 1.1.4.dev0) as our SDD toolkit. Spec Kit adds a set of slash commands to a coding agent, one per step of the workflow:

| Command | What it produces |
|---|---|
| `/speckit-constitution` | `constitution.md`: the project's non-negotiable rules |
| `/speckit-specify` | `spec.md`: stakeholders, user stories, numbered requirements and acceptance criteria |
| `/speckit-clarify` | Questions about anything still ambiguous; the answers are written back into `spec.md` |
| `/speckit-plan` | `plan.md`, `research.md`, `data-model.md`, the API contract and `quickstart.md` |
| `/speckit-tasks` | `tasks.md`: ordered, numbered tasks grouped by user story |
| `/speckit-implement` | The code, built task by task, with each task marked done |

We chose Spec Kit for three reasons:

- **It works inside the agent we already used.** Spec Kit has a Claude Code integration, so we could use the same agent and model as in the vibe version. That keeps the comparison fair: the difference between the two versions is the process, not the tool.
- **Every step leaves a file.** The constitution, spec, plan and tasks are Markdown files in the repository. We reviewed them in pull requests like code, and they stay as evidence of what was decided and when.
- **It has a clarify step.** In the vibe version the agent filled every gap in the prompt with its own choices. Spec Kit's clarify step makes the agent ask instead, so we make those decisions.

Spec Kit's templates are general, so we adapted them through our prompts. The spec template has no stakeholder section or numbered non-functional requirements, so the specify prompt asked for both. Spec Kit treats tests as optional, so the constitution and the tasks prompt made tests-first mandatory.

### 4.2 Development Environment

| Part | What we used | Why |
|---|---|---|
| Operating system | Windows 11 | Our own desktop PCs. The plan also targets macOS and Linux, and CI runs on Ubuntu, so the code doesn't depend on Windows. |
| Editor | VS Code | Opens the Markdown specs and Python code side by side, and Claude Code integrates with it. |
| Coding agent | Claude Code with Claude Opus 5.5 (`claude-opus-5-5`) | Runs the Spec Kit commands, reads and edits the repository, and runs the tests itself, so it can check its own work. The same agent and model built the vibe version. |
| SDD toolkit | Spec Kit 1.1.4.dev0, installed into `sdd/` | See 4.1. Its commands and templates live in `sdd/.claude/` and `sdd/.specify/`. |
| Python and packages | Python 3.12, managed with uv | `uv sync --locked` installs the exact versions from `uv.lock`, so our machines and CI run the same code. |
| Version control | Git and GitHub | Every change went through a branch, a pull request linked to an issue, a review and a merge (see section 6). |
| CI | GitHub Actions (`.github/workflows/sdd-tests.yml`) | Runs the whole test suite with coverage on every pull request and every push to `main`, and fails below 80% coverage, so a failing test shows on the pull request before it is merged. |

The vibe version (`vibe/`) and the SDD version (`sdd/`) live side by side in one repository, each with its own dependencies. This let us run the same acceptance tests against both.

### 4.3 Deriving the requirements using the IDE/coding agents

We derived the requirements in two steps with Claude Code and Spec Kit, and reviewed the result before any design work started.

**1. Specify.** The specify prompt (quoted in 2.6) gave the agent the same feature list as our vibe prompt, plus three instructions of our own: list the stakeholders, add numbered NFRs for security, reliability, performance and usability, and leave the rules we hadn't decided as open questions. The agent turned this into five prioritised user stories, each with acceptance scenarios in Given/When/Then form, and derived the numbered requirements from them: FR-001 to FR-017 and NFR-001 to NFR-008. It marked three rules `[NEEDS CLARIFICATION]`: opening hours and maximum length, editing bookings, and deactivating rooms with bookings. We answered those. Spec Kit's quality checklist (`checklists/requirements.md`) scored the spec 14/16 until the answers were in.

**2. Clarify.** The clarify prompt pointed the agent at the areas where the vibe version had failed:

```text
/speckit-clarify Check the spec for anything still ambiguous, with extra attention to security and reliability (login abuse, tokens, input limits) and to the availability rules now that opening hours exist.
```

The agent asked four questions, each with a recommended answer. We chose the answers below, and the agent wrote each one back into the spec. The checklist then scored 16/16.

- Q: Should the system limit repeated failed logins? → A: Slow down, never lock: after 5 failures for a username within 15 minutes, each further attempt for it waits 2 seconds first.
- Q: How far ahead can a booking be made? → A: The start must be within 90 days from now.
- Q: When a user asks for a room's availability on a date, which hours does the answer cover? → A: The date is a Helsinki calendar date, and the answer covers that day's opening hours, 08:00–18:00.
- Q: Do users need to log out, ending a token before its 60 minutes are up? → A: No. There is no logout; tokens are valid until they expire.

The first answer created a new requirement, NFR-009 (slow down repeated failed logins, never lock the account). It also exposed a conflict: NFR-006 says every request finishes within 500 ms, but NFR-009 deliberately waits 2 seconds. We fixed this in the spec, by exempting delayed logins from NFR-006, before planning started.

> **Note:** As in 2.6, the prompt log credits these answers to Ivar Lehvonen alone because we worked through Ivar Lehvonen's Claude account. We decided them together.

The template lists several activities for this step. This is how each one was covered:

| Activity | Where it is | How it was produced |
|---|---|---|
| Software requirements specification | `sdd/specs/001-room-booking-api/spec.md` | Specify, then clarify |
| System constraints | FR-012 (08:00–18:00, at most 4 hours), FR-011 (at most 90 days ahead), FR-002 (password length), and the constitution (no other services, Python 3.11+) | Our answers to the open and clarify questions; the constitution |
| Interfaces | `contracts/api.md` and `docs/openapi.json` (see 2.5) | Plan step, from the requirements |
| Acceptance criteria | One under every FR and NFR, plus the user stories' scenarios and five measurable success criteria (SC-001 to SC-005) | Specify; checked by Spec Kit's quality checklist |
| Compliance requirements | The constitution's five principles, checked by the plan's "Constitution Check" before and after design | Constitution step; plan step |

### 4.4 SDD Workflow and Implementation

We used Spec Kit's own workflow and added two rules from our constitution: tests are written and committed before the code, and every change goes through a reviewed pull request.

```text
constitution → specify → clarify → plan → tasks → (for each issue group: failing tests → implementation → review and merge)
```

**Specification (PR #22).** Constitution, specify, clarify, plan and tasks ran in one branch. The tasks step produced 37 numbered tasks in eight phases (`tasks.md`), and grouped them into six issues, so that each group became one reviewable pull request:

| Group | Issue | Tasks | Covers |
|---|---|---|---|
| A. Project setup and foundation | #16 | T001–T013 | constitution, NFR-002 base |
| B. Accounts | #17 | T014–T016 | US1, FR-001–FR-006 |
| C. Bookings | #18 | T017–T020 | US2, FR-011–FR-013, FR-017, NFR-005 |
| D. Rooms, availability and my bookings | #19 | T021–T026 | US3, US4, FR-007, FR-010, FR-014–FR-016 |
| E. Admin | #20 | T027–T028 | US5, FR-008, FR-009, NFR-003 |
| F. NFRs, traceability, docs | #21 | T029–T037 | NFR-001, NFR-004, NFR-006, NFR-007, NFR-009, SC-001–SC-005 |

**Implementation (PRs #23–#28).** Each group was built with one `/speckit-implement` prompt that named only that group's tasks and ended with "do not continue after T0xx", so the agent couldn't run ahead. Every story followed the same order:

1. The agent wrote the acceptance tests from the spec's scenarios and ran them.
2. The tests were committed while they still failed, so the Git history shows they came first.
3. The agent implemented the tasks until all tests passed, and marked the tasks done in `tasks.md`.
4. The pull request was reviewed with the help of an AI (Claude Code), CI ran the full suite, and we merged it.

| PR | Group | Tests failing when committed | All tests passing after | Coverage after |
|---|---|---|---|---|
| #23 | A. Setup and foundation | — (no stories yet; one health smoke test) | 1 | 40% |
| #24 | B. Accounts | 23 | 24 | 74% |
| #25 | C. Bookings | 24 | 68 | 92% |
| #26 | D. Rooms, availability, my bookings | 31 | 100 | 93% |
| #27 | E. Admin | 25 | 125 | 95% |
| #28 | F. NFRs and evidence | 3 (of 61 new) | 186 | 94.83% |

**Reviews fed the next prompt.** What we found in one review went into the next group's prompt:

- The review of #23 found that failed-login usernames were stored as typed. Group B's prompt added "lower-case and limit to 50 characters the username stored in failed_logins".
- The review of #24 found that a successful login should clear earlier failures. Group F's prompt added it to the slow-down.
- The review of #26 found that admin cancelling was implemented but untested. Group E's prompt asked for tests of an admin cancelling any user's booking and an ended booking.

**Where the workflow needed correcting.** Three things didn't go as planned, and each was fixed in the process rather than patched afterwards:

- The generated task list put the 80% coverage gate in the first group, which would have failed CI on every pull request until the last one. We moved it to group F before any code was written.
- In groups C and D, some "not found" tests passed before the endpoint existed, because FastAPI also answers 404 for a missing route. The tests now check the error message too, so they fail until the real endpoint exists.
- In group F, 58 of the 61 new NFR tests passed immediately, because the earlier stories had already built those properties in (bounded IDs, the 90-day check, documented errors). Only the login slow-down was truly test-first there. Mutation checks showed that the tests still catch the faults they guard against (see 5.1).

### 4.5 Prompts

All 11 SDD prompts were run with Spec Kit 1.1.4.dev0 through Claude Code (`claude-opus-5-5`) on 2026-10-16. The full log, with each prompt verbatim and its purpose, reasoning, expected result, what came back, issues and refinements, is in [`docs/sdd/prompt-log.md`](../sdd/prompt-log.md).

| # | Command | Purpose | What came back | Issues and refinements |
|---|---|---|---|---|
| 1 | `/speckit-constitution` | Fix the non-negotiable rules before any spec exists | Constitution v1.0.0: five principles (Specification First, Test-First, Secure by Default, Explicit Time Handling, Simplicity) | None |
| 2 | `/speckit-specify` | Turn the vibe feature list into numbered, testable requirements | 5 stakeholders, 5 user stories, FR-001–FR-017, NFR-001–NFR-008, 3 open questions | The open questions were answered by the team |
| 3 | `/speckit-clarify` | Find remaining ambiguities before planning | 4 questions answered: login slow-down (new NFR-009), 90-day horizon, availability hours, no logout | Exposed a conflict between NFR-006 and NFR-009, fixed in the spec |
| 4 | `/speckit-plan` | Fix the technical design | plan, research decisions R1–R8, data model, API contract, quickstart | None |
| 5 | `/speckit-tasks` | Break the plan into ordered, test-first tasks | 37 tasks in 6 issue groups (A–F, issues #16–#21) | None |
| 6 | `/speckit-implement` group A | Project setup and foundation (T001–T013) | All 13 tasks done; coverage 40% | Coverage gate moved to T035 so CI could pass from the start |
| 7 | `/speckit-implement` group B | User Story 1, register and log in (T014–T016) | 23 tests committed failing, then all pass; coverage 74% | None |
| 8 | `/speckit-implement` group C | User Story 2, book a room (T017–T020) | 68 tests pass; coverage 92%; mutation check proves the concurrency test | Two 404 tests first passed for the wrong reason; fixed to check the message |
| 9 | `/speckit-implement` group D | User Stories 3 and 4 (T021–T026) | 100 tests pass; coverage 93% | Same wrong-reason 404 issue, fixed the same way |
| 10 | `/speckit-implement` group E | User Story 5, admin (T027–T028) | 125 tests pass; coverage 95% | None |
| 11 | `/speckit-implement` group F | NFRs, traceability, OpenAPI export, evidence runs (T029–T037) | 186 tests pass; coverage 94.83%; SDD 155/155 vs vibe 114/155 over HTTP | Most NFR tests passed before new code; the slow-down's first design would have blocked other requests |

Prompts 1–9 were AI-drafted and edited and approved by both Ivar and Kristoffer (we edited the wording of 7–9 before running them). Prompts 10 and 11 were run by us in our own wording.

> **Note:** The prompt log ([`docs/sdd/prompt-log.md`](../sdd/prompt-log.md)) says that Ivar Lehvonen approved, edited or ran these prompts. In reality we did this together. We worked through Ivar Lehvonen's Claude account, so the AI-written logs give the credit to the account holder alone.

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
