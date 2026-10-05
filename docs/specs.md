# IntelliHire — Master Completion Specification

**Status:** Read-only architecture audit. No application code was modified to produce this document.
**Audit date:** 2026-10-03
**Audited by:** Multi-agent repository re-scan (9 independent read-only research passes) over `D:\Sem 5\SGP\IntelliHire`.

---

## 1. Purpose

This document is the master implementation roadmap for finishing IntelliHire. It is not a redesign proposal. Its job is to:

1. State exactly what exists today, backed by file:line evidence.
2. Compare the AI Interview Engine against its two frozen architecture documents and classify every gap.
3. Map how connected the frontend is to the backend, feature by feature, with concrete contract mismatches.
4. Identify genuinely dead/legacy code (proven via import/route search, never by filename guesswork) versus code that looks old but is live.
5. Produce an atomic, dependency-ordered, one-task-at-a-time roadmap to close the gaps safely.

The guiding principle: **finish the existing system by aligning it with the frozen architecture and connecting the remaining frontend/backend seams — do not rewrite working subsystems, do not create a second engine, do not delete anything without proof of non-use.**

---

## 2. Source-of-Truth Documents

- `IntelliHire_Interview_Strategy_Architecture.docx` — the frozen policy/decision-layer architecture for the Official Interview Engine (interview types, strategies, topic prioritization formula, evidence model, reporting contract).
- `IntelliHire_Prompt_Library_v1.docx` — the frozen prompt-assembly specification for the single `LLMQuestionGenerator` (16 valid strategy×type combinations, block architecture, exact prompt text).

Both were read in full for this audit. Where the current code diverges from these documents, the divergence is recorded in §6, §12, §13 with a classification (must fix / acceptable deviation / stricter-than-spec) — the documents are never silently reinterpreted.

---

## 3. Current Repository Snapshot

```
D:\Sem 5\SGP\IntelliHire\
├── backend/            FastAPI + MongoDB (Motor), Python 3.11
│   └── app/
│       ├── ai_interview/     the Official + Practice interview engine (Phases 1–9)
│       ├── api/               ~45 routers: admin/, company/, recruiter/, auth.py, interview.py, ws.py, candidate_portal.py, resume.py, admin_proxy.py
│       ├── auth/, rbac/       JWT + 2-layer RBAC
│       ├── db/                 Motor client, bootstrap, indexes, Pydantic "storage" models
│       ├── repositories/      ~25 thin Motor CRUD wrappers
│       ├── services/          ~16 business-logic services
│       ├── schemas/            request/response DTOs, decoupled from db/models.py
│       ├── resume_processing/, speech/, analytics/, reports/, validation/, middleware/, core/
│       └── main.py
│   └── tests/            110 test files (66 ai_interview, 26 integration, 4 api, 14 unit)
├── frontend/           React 19 + Vite, React Query, react-router-dom 7
│   └── src/
│       ├── api/*.js           fetch-based client (candidate/admin calls)
│       ├── services/**/*.js   axios-based client (company/recruiter calls)
│       ├── pages/{admin,company,candidate,recruiter}/
│       ├── components/{admin,company,candidate,common,charts,layout}/
│       ├── context/, hooks/, routes/, mock/, data/, utils/, styles/
│   └── 5 test files total, all candidate-interview-area
├── docker-compose.yml   0 bytes — empty
└── IntelliHire_Interview_Strategy_Architecture.docx, IntelliHire_Prompt_Library_v1.docx, IntelliHire_SDD.pdf, IntelliHire_SRS_Final.pdf
```

Stack confirmed: FastAPI/Motor/MongoDB, JWT (HS256, python-jose/passlib), LLM = Groq (`openai/gpt-oss-20b`, OpenAI-compatible adapter) with OpenAI `gpt-4o-mini` fallback, Speech = Sarvam AI (Saaras STT, Bulbul TTS), React 19/Vite/React Query/Tailwind-configured-but-unused.

---

## 4. Current System Architecture

Confirmed live data/control flow (from `app/main.py` lifespan through to transport):

```
Campaign configuration (company/campaigns.py)
    ↓
CampaignStrategySnapshot embedded on campaign doc (immutable copy, not a reference)
    ↓
SessionCreationService.create_session() — snapshots strategy + voice_id onto InterviewSessionSchema
    ↓
SessionInitializer.initialize() — builds TopicProgress[] from blueprint (resume_evidence tagging)
    ↓
RuntimeController.get_allowed_action() — state machine facade
    ↓  (official mode)                              ↓ (practice mode)
TopicProgressionEngine → ShadowPriorityCalculator    Rigid sequential topic walk (no priority calc)
    ↓
QuestionTurnPlanner → category/budget gate
    ↓
QuestionRequestBuilder → minimized LLM request
    ↓
PromptResolver (16-combination registry) → assembled prompt
    ↓
LLMQuestionGenerator → OpenAICompatibleAdapter (Groq)
    ↓
QuestionValidator → DuplicateDetector → QuestionDispatcher (persists)
    ↓
TTS (Sarvam Bulbul, session-snapshotted voice_id) → WebSocket question_ready event
    ↓
Candidate records answer → STT (Sarvam Saaras, REST not WS) → submit_answer WS command
    ↓
AnswerEngine (AnswerProcessor → EvaluationRequestBuilder → LLMAnswerEvaluator → EvaluationValidator → CoverageAssessor → EvaluationApplicator)
    ↓
AdaptiveDifficultyEngine.adapt() / FollowUpPolicyEngine.decide_followup()
    ↓
CompletionEngine.evaluate() (official: strategy-driven; practice: legacy fixed-3)
    ↓
InterviewResultService.generate_result_report() — READ-ONLY aggregation, zero LLM calls
    ↓
Company/Candidate report pages (REST GET)
```

This matches the architecture document's intended insertion point ("a data-driven policy plus the deterministic function that consumes it, inserted between TopicStateManager and QuestionEngine/CompletionEngine") — confirmed, not a second engine.

---

## 5. Actual End-to-End Interview Flow (with evidence per hop)

| Hop | Code | API | Schema | Frontend | Test |
|---|---|---|---|---|---|
| Campaign creation | `backend/app/api/company/campaigns.py:31` | `POST /company/campaigns` | `CampaignCreateRequest` (`schemas/company.py:23-56`) | `pages/company/NewCampaign.jsx` | None found |
| Strategy snapshot | `campaigns.py:104,362` builds `CampaignStrategySnapshot`, stored on campaign doc | — | `db/models.py:290` | n/a (invisible to user) | None found |
| Candidate invitation | `company/candidates.py:41` `POST /invite` | — | `InviteCandidateRequest` | **Broken** — `candidateService.js` has no `inviteCandidate()`; `Candidates.jsx:268` calls a method that doesn't exist | None found |
| Resume upload + processing | `candidate_portal.py:50` → `ResumeProcessingService` → `app/resume_processing/{parser,cleaner}.py` (legacy pipeline, confirmed live) | `POST /api/candidate/resume` | `ResumeUploadResponse` | `Resume.jsx` | None found |
| Interview start (official) | `interview.py:68` `SessionCreationService.create_session` | `POST /api/interview/campaigns/{id}/sessions` | — | `InterviewRoom.jsx:92-99` | None found |
| Session init + strategy snapshot copy | `session_creation_service.py:236,269,274` | — | `InterviewSessionSchema` | — | `tests/ai_interview/persistence/*` |
| First question / prompt resolution | `question_engine.py` → `resolver.py:97-106` | WS `question_ready` event | `ws_events.py:110-118` | `InterviewRoom.jsx:260-269` reads only 2 of 7 available fields | Mocked WS only |
| LLM generation | `llm_question_generator.py` → `OpenAICompatibleAdapter` | — | — | — | `tests/ai_interview/llm_infrastructure/*` |
| Question validation | `question_validator.py` (real, `app/ai_interview/question_engine/`) | — | — | — | `test_question_validator.py` |
| TTS | `interview.py:397` | `POST /api/interview/sessions/{id}/questions/{qid}/speech` | — | `useTextToSpeech.js:93-101` | Mocked only |
| Candidate answer (voice) | `useAudioRecorder` → `audioConversion.js` → `useSpeechRecognition.js:73-87` | `POST /api/interview/sessions/{id}/questions/{qid}/transcribe` | — | `VoiceControls.jsx` | Mocked only |
| submit_answer | `ws_commands.py:63-83` | WS command | matches field-for-field | `useInterviewSession.js:154-170` | Mocked WS |
| AnswerEngine → EvaluationRecord | `answer_engine.py` full pipeline | — | `answer_engine/schemas.py` | — | extensive backend tests |
| Evidence persistence | `evaluation_applicator.py:39-49` | — | `TopicProgress.{resume_evidence,candidate_claim,interview_evidence}` | — | backend tests only |
| Difficulty/follow-up/priority | `adaptive_difficulty_engine.py`, `followup_policy_engine.py`, `shadow_priority_calculator.py` (live, not shadow) | — | — | — | backend tests only |
| Completion | `completion_engine.py` | WS `interview_completed` event | `InterviewCompletedData` | `useInterviewSession.js:126-128` → navigates | backend tests only |
| Result | `interview_result_service.py:69-162` | `GET /api/interview/sessions/{id}/report` | ad-hoc dict, NOT the declared `ReportResponse` schema (see §10) | `Reports.jsx` (candidate), `CandidateReport.jsx` (company) | None found |
| Company report | `company/candidates.py:332` | `GET /company/candidates/interviews/{session_id}/results` | same dict as above | `CandidateReport.jsx:47` | None found |
| **InterviewComplete page** | — | — | — | **`InterviewComplete.jsx` is a static mock page — discards the real `questions_asked_total`/`completed_at` event data and renders hardcoded "38 min" / placeholder questions** | — |

**Missing links identified:** candidate invitation (frontend method doesn't exist), practice-completion REST call (hook defined but never invoked — see §14), InterviewComplete page ignoring real completion data, evidence fields (`resume_evidence`/`candidate_claim`/`interview_evidence`) never reaching either report consumer despite being fully populated upstream.

---

## 6. Final Architecture Compliance Matrix

Status values: COMPLETE / PARTIAL / MISSING / CONFLICTING / NOT VERIFIED.

| Architecture Requirement | Current Implementation | Status | Evidence | Remaining Work | Priority |
|---|---|---|---|---|---|
| StrategyDefinition model | `ai_interview/schemas/strategy.py:36-76` | COMPLETE | All spec fields present; `critical_topic_max_followups` is an extra, harmless addition | None | — |
| Strategy versioning | `api/admin/strategies.py` full version CRUD | COMPLETE | 7 endpoints incl. `POST .../versions`, `PATCH .../activate` | **Admin UI to use these endpoints does not exist** (see §8) | P1 |
| Campaign strategy snapshot | `CampaignStrategySnapshot`, embedded not referenced | COMPLETE | `company/campaigns.py:104,362`; `db/models.py:290` | None | — |
| 5 Interview Types | `core/enums.py:78-83` InterviewType enum | PARTIAL | Enum has all 5; Situational/Case has no topic-generation path | Build situational topic/scenario source (§12) | P1 |
| 6 Strategies | strategy_ids as data, not a Python enum | COMPLETE | Verified against `registry.py` + `prompt_library.py` | None | — |
| Mixed composition (soft weighting) | `shadow_priority_calculator.py:76-85` reads `session.mixed_composition` | COMPLETE | Matches spec exactly — composition is a priority term, not a bucket allocator | None | — |
| Criticality multipliers (1.5/1.2/1.0/0.7) | `shadow_priority_calculator.py:51-59` | COMPLETE | Exact match | None | — |
| Priority formula (4-term weighted sum) | `shadow_priority_calculator.py:98-105` | COMPLETE | Formula matches spec term-for-term | Rename module — it is live/authoritative, not "shadow" (cosmetic, but causes confusion); comment at `topic_progression_engine.py:32` literally says "Cutover: Shadow priority becomes authoritative" | P3 |
| Deterministic decision function (`decide_next_action`) | Split across `CompletionEngine` (stop/continue) + `TopicProgressionEngine` (topic pick) + `QuestionTurnPlanner`/`FollowUpPolicyEngine` (category) | PARTIAL | Functionally equivalent outcome; spec described one recursive function, code uses 4 coordinating modules | Acceptable deviation — do not force a rewrite into one function; document the mapping instead (done here) | P3 |
| Resume/Requirement evidence 3-way model | `resume_evidence`/`candidate_claim`/`interview_evidence` declared + populated at every hop from `core/enums.py` through `TopicProgress` and `EvaluationRecord` | PARTIAL | `evaluation_applicator.py:39-49` confirms population; **dropped entirely at `interview_result_service.py`** | Thread evidence into the report (§12, §17) | **P0** |
| Claim ≠ proof enforcement | No code path auto-upgrades `candidate_claim` text to `interview_evidence=STRONG` | COMPLETE | Verified — `interview_evidence` only ever set from live LLM evaluation (`evaluation_normalizer.py:44`) | None | — |
| Budget cross-validation (`max_per_topic × critical_count ≤ max_questions`) | Not implemented anywhere | MISSING | Searched `strategy.py`, `blueprint_validator.py`, `api/admin/strategies.py` — zero matches | Add validator (§12) | P2 |
| 16 prompt combinations | `question_engine/prompts/registry.py:15-43` | COMPLETE | All 16 IDs verified present, in spec order | None | — |
| Prompt block assembly order | `resolver.py:97-106` | COMPLETE | `M0_COMMON + S + D + ENV + C + ADD + OUTPUT_CONTRACT` matches exactly | None | — |
| M0_COMMON grounding rules | `prompt_library.py:3-30` | COMPLETE | Substance matches (wording differs, intent identical) | `prior_questions_on_topic` is stated as a rule but never actually injected as data anywhere in `resolver.py` — rule exists without backing data | P2 |
| CONTEXT_META (optional, default off) | Absent entirely | MISSING (stricter than spec) | Grep returns zero hits | Acceptable — spec defaults this off anyway; no action required unless budget-context-in-prompt becomes desired later | P3 |
| Category×dimension / category×strategy validity | 3 explicit rules in `resolver.py:50-55` + per-combo whitelist in `registry.py` | PARTIAL | Covers spec's key examples (technical_challenge, correction-excludes-behavioral, gap_verification) but is ad hoc, not a declared matrix | Low priority — current behavior is correct for all 16 live combos | P3 |
| Situational dimension prompts | `D.situational`, `ENV.situational`, all `C.*.situational` blocks exist in `prompt_library.py`/`blocks.py` | PARTIAL | Templates fully built | `scenario_context` hardcoded `None` at both call sites in `question_turn_planner.py:198,244`; `blueprint_planning/` never produces a situational topic | Build scenario bank + situational topic source (§12) | P1 |
| Adaptive difficulty (per-topic, resets on switch) | `adaptive_difficulty_engine.py` | COMPLETE | Matches spec behavior | None | — |
| Behavioral specificity flag | `BehavioralSpecificity` enum (GENERAL/SPECIFIC/EVIDENCE_REQUIRED) | COMPLETE | Matches spec's 3-state model | None | — |
| Follow-up policy (deterministic, LLM advisory only) | `followup_policy_engine.py` | COMPLETE | `followup_recommended` is read as a hint, never authoritative | None | — |
| Completion (min/target/max/critical/terminal/coverage) | `completion_engine.py:119-205` | COMPLETE (official) / COMPLETE (practice, separate legacy path) | Both paths traced and confirmed isolated | None | — |
| Gap verification (resume-absent requirements) | `GV_TECH`/`GV_MIXED` prompt family + `question_turn_planner` gap logic | COMPLETE | Matches spec's stage A/B claim handling | None | — |
| Voice allowlist (shubh/simran/rohan/ishita/sunny) | 5 separate hardcoded declarations | COMPLETE | Verified identical set in all 5 locations | **Duplication risk** — 5 independent hardcoded copies instead of 1 shared constant | P2 (dedupe, not a bug) |
| Session voice snapshot + stability | `session.voice_id` field, TTS endpoint prioritizes session snapshot over live campaign | COMPLETE | `api/interview.py:437-458` confirmed session snapshot always wins when present | None | — |
| Practice Mode — exactly 3 questions | `session_creation_service.py:167-208` sets `total_question_budget=3` | COMPLETE (count) | Confirmed | None | — |
| Practice Mode — exact topic wording | Two conflicting hardcoded text sources (`session_creation_service.py` topic_name vs `question_engine.py:136-146` actual delivered text) | CONFLICTING | Neither matches the specified "Introduction and Background / Recent Experience and Work / Proudest Project or Contribution" wording, and the two sources disagree with each other | Reconcile to one source of truth; align wording with product decision (§14) | P1 |
| Practice isolation from official engine | `mode_id == "practice"` branches in every subsystem | COMPLETE | Traced through completion_engine, runtime_controller, followup_policy_engine, interview_turn_coordinator, topic_selector | None | — |
| Campaign voice applies to Practice | `session_creation_service.py:274` | COMPLETE | Unconditional read of `campaign.get("voice_id")`, correctly falls back to default only when no campaign | None | — |
| Reporting: 3-way evidence, topic coverage, skip reasons | `interview_result_service.py` output dict | MISSING | Confirmed: output keys are only score/count/qualitative-threshold-derived fields; no evidence fields, no `skip_reason`, no `followup_depth`, no `followup_categories_used[]` | Full report rebuild required (§12, §17) | **P0** |
| Analytics / Explainability (decision traces surfaced to admin) | `CompletionDecisionTrace`/`FollowUpDecisionTrace`/`DifficultyDecisionTrace` exist internally | MISSING (UI) | Traces are computed and logged but never surfaced in any admin/company UI | Build an explainability view (§19) | P2 |

---

## 7. Backend Status

Confirmed live (see §3 and the prior full-repo scans this audit built on): ~45 routers, JWT auth, 2-layer RBAC (`UserRole` + `SubRole`/`Permission` matrix, loosely connected), Motor/MongoDB with OCC+fencing+idempotency for the interview engine specifically, 16 business-logic services, bootstrap seeding (hardcoded dev admin `admin@intellihire.dev` / `admin123` — confirm rotated before any production use).

Key weak points found this pass (see §18 for full detail): refresh-token flow is dead end-to-end despite server-side storage; `/api/auth/logout` is a no-op and bypassed by every role except admin; `GET /api/auth/profile` returns hardcoded values; JWT claims never include `name`/`email`, so `AuthContext.user.name/.email` are permanently blank; PDF/CSV export generation is entirely fake (dummy bytes or mislabeled plaintext) despite WeasyPrint/Jinja2 being installed and never imported.

---

## 8. Frontend Status

React 19 + Vite confirmed live. Two parallel, non-unified API client styles: fetch-based `src/api/*.js` (no `/api` auto-prefix, manual bearer token) and axios-based `src/services/**/*.js` (separate base URL config, auto-attaches token from `localStorage`). Both are in active, overlapping use — not a dead-vs-live situation, a genuine duplication that should be consolidated (§22).

**Confirmed dead/stub pages** (unrouted, verified via `CandidateRoutes.jsx`/`App.jsx` import lists):
- `pages/candidate/ResumeUpload.jsx`, `InterviewSetup.jsx`, `ReportView.jsx`, `Registration.jsx` — all `return null;`, not imported by any route.
- `pages/recruiter/ChangePassword.jsx` — not imported anywhere; `App.jsx` routes to `pages/company/ChangePassword.jsx` instead.
- `routes/CompanyRoutes.jsx` — defined, never imported.
- `components/recruiter/` — empty directory.

**Confirmed mock-data / non-functional pages:**
- `pages/admin/Analytics.jsx` — 100% hardcoded data; `AnalyticsAPI` client is fully wired but never called from this page.
- `pages/candidate/InterviewComplete.jsx` — static placeholder, discards real completion event data, imports from `data/candidate/placeholderData`.
- `pages/company/CampaignDetail.jsx` — "Quick Stats" are fabricated percentages of applicant count (`* 0.18`, `* 0.08`, `* 0.02`), not real data.
- `pages/admin/PlatformSettings.jsx` "Strategies" tab — 4 cosmetic toggles unrelated to any real `strategy_id`.

**Settings page is functionally broken:** 5 of 7 toggles in `pages/candidate/Settings.jsx` use field names that don't match the backend schema (`sidebar_collapsed` vs `sidebar_auto_collapse`, `email_notifications` vs `interview_reminders`, `sms_notifications` vs `company_updates`, `language` vs `portal_language`, `subtitles` vs `live_subtitles`) — these toggles silently do nothing and always render as off.

---

## 9. Frontend ↔ Backend Integration Matrix

Legend: ✅ connected and correct · ⚠ connected with a bug · ❌ not connected / broken · — not applicable or not independently verified this pass.

| Feature | Backend | API | Frontend | Connected | Tested | Remaining |
|---|---|---|---|---|---|---|
| Login | ✅ | ✅ | ✅ | ✅ | Backend only (`test_auth_smoke.py`) | None functionally; see §7 for `name`/`email` bug |
| Register | ❌ (route doesn't exist) | ❌ | ❌ | ❌ | — | Feature not built — confirm whether in scope at all |
| Refresh | ⚠ (scaffold, hardcoded response) | ⚠ | ❌ (never called) | ❌ | None | Build real refresh flow or remove the dead storage/plumbing |
| Logout | ⚠ (no-op server-side) | ⚠ | ⚠ (only admin calls it) | ⚠ | None | Implement real token revocation; wire all roles to call it |
| Admin dashboard | ✅ | ✅ | ✅ | ✅ | Generic only | None |
| Admin company CRUD | ✅ | ✅ | ✅ | ✅ (except 4 endpoints never called — stats/permissions/subscription/usage-reset) | None | Wire the 4 unused endpoints or confirm intentionally unused |
| Admin candidate management | ✅ | ✅ | ⚠ | ⚠ | None | `AdminCandidates.jsx`/`AdminCandidateDetail.jsx` render fields (`readiness_score`,`risk_score`,`activities`) that nothing in the backend guarantees — likely always blank |
| Admin strategy management | ✅ (full CRUD+versioning) | ✅ | ❌ (no real UI exists) | ❌ | Backend only | **Build the admin strategy authoring UI — see §25 recommended next task** |
| Admin subscription management | ✅ | ✅ (dedicated endpoint) | ⚠ (wizard bypasses dedicated endpoint, uses generic PATCH instead) | ⚠ | None | Wire `SubscriptionTab` to the dedicated endpoint, or confirm generic PATCH is sufficient |
| Admin security logs | ✅ | ✅ | ⚠ (filters UI present but non-functional) | ⚠ | None | Wire search/severity filters and Export button |
| Admin analytics | ✅ | ✅ (fully wired client) | ❌ (page never calls it) | ❌ | None | Replace hardcoded data with real `AnalyticsAPI` calls |
| Company dashboard/profile | ✅ | ✅ | ✅ | ✅ | None | None |
| Company campaign create/edit | ✅ | ✅ | ⚠ ("adaptive" difficulty option causes 422) | ⚠ | None | Remove invalid dropdown option or add it to backend enum |
| Company candidate invitation | ✅ | ✅ | ❌ (method doesn't exist in service) | ❌ | None | Add `inviteCandidate()` to `candidateService.js` |
| Company candidate status actions (suspend/activate/reset) | ✅ | ✅ | ❌ (3 of 6 service methods missing) | ❌ | None | Add missing service methods |
| Company team/recruiter mgmt | ✅ | ✅ | ⚠ (status-casing bug + duplicate UI) | ⚠ | None | Fix casing bug; consolidate Recruiters.jsx/Team.jsx |
| Company reports | ✅ (data) / ❌ (PDF) | ✅ | ⚠ (download buttons hit fake PDF stubs) | ⚠ | None | See §18 PDF generation |
| Company subscription/payment | ✅ (simulated) | ✅ | ✅ (internally consistent simulator) | ✅ (as a simulator) | Payment: 0 tests | Decide: real gateway or keep simulated for demo (§21 boundary, not redesigned here) |
| Candidate resume upload/processing | ✅ | ✅ | ✅ | ✅ | None | None |
| Candidate practice mode | ✅ | ✅ | ⚠ (completion hook never invoked) | ⚠ | Mocked only | Wire `useCompletePractice` call (§14) |
| Candidate official interview (WS) | ✅ | ✅ | ✅ | ✅ | Mocked only (no real-wire contract test) | Add a contract test against real Pydantic WS schemas |
| Candidate STT/TTS | ✅ | ✅ | ✅ | ✅ | Mocked only | None functionally |
| Candidate settings | ✅ | ✅ | ❌ (5/7 field-name mismatches) | ❌ | None | **Fix field names — see §25 candidate**, concrete one-file fix |
| Candidate interview completion page | ✅ (real event data available) | — | ❌ (static mock page) | ❌ | None | Rebuild `InterviewComplete.jsx` from real event/report data |
| Candidate result/report | ✅ (data-driven) | ✅ | ✅ (reads actual service output, not the stale declared schema) | ✅ | None | Evidence fields still missing from the underlying report (§6) |
| Recruiter self-service (own campaigns/candidates/dashboard/interviews) | ✅ (4 full routers) | ✅ | ❌ (zero frontend calls — recruiters use the Company portal instead) | ❌ | None | Decide: build a dedicated recruiter portal, or delete these 4 routers as intentionally superseded by the Company-portal-for-recruiters model (needs a product decision, not a code decision) |
| Recruiter profile/password | ✅ | ✅ | ✅ (via Company-portal pages) | ✅ | None | None |

---

## 10. API Contract Audit

Full concrete mismatch table (frontend call vs backend route), consolidated from the dedicated audit pass:

| Frontend Call | Backend Route | Contract Match | Problem | Fix |
|---|---|---|---|---|
| `PATCH /admin/settings/master` (`api/settings.js:19-24`, `updateMasterSettings()`) | Only `GET /master` exists in `admin/settings.py` | **No** | 404/405 on every call | Add the PATCH route, or remove the dead frontend function |
| `GET /company/team/${id}` (`recruiterManagementService.js:20`, `getRecruiter(id)`) | No single-member GET route in `team.py` (only list and sub-resource routes) | **No** | 404 | Add `GET /company/team/{member_id}`, or filter client-side from the list call |
| `POST /company/candidates/${id}/send-invite` (`candidateService.js:40`) | Only `POST /company/candidates/invite` (body-driven, different semantics) exists | **No** | 404 | Implement the per-candidate re-invite route, or repoint the frontend to `/invite` |
| `GET /company/candidates/${id}/resume` (`candidateService.js:43-46`, `downloadResume`) | No matching route | **No** | 404 | Add the route or remove the dead button |
| `GET /company/candidates/${id}/report` (`candidateService.js:48-51`, `downloadReport`) | No matching route (closest is session-keyed `/interviews/{session_id}/results`) | **No** | 404 | Add candidate-keyed route or repoint to the session-keyed one |
| `candidateService.suspendCandidate/activateCandidate/resetCredentials/inviteCandidate/bulkAssignCandidates` (called from `Candidates.jsx`/`CandidateDetails.jsx`) | Backend routes **do** exist (`candidates.py:611,647,782,808,834,155,41`) | **No** (frontend-side — methods never defined in `candidateService.js`) | `TypeError`, never reaches network | Add the 5 missing service wrapper functions |
| `changeSubscription(features, limits, billing_cycle)` / `verifyChangePayment(...)` (`api/subscription.js:11-18`) called with 7/10 args from `ChangeSubscription.jsx` | Backend accepts `allowed_languages/voices/llm_tiers/interview_modes` as optional fields | **Partial** | Extra args silently dropped — AI-config changes on subscription upgrade/downgrade are never persisted | Add the missing named parameters to the wrapper functions |
| `api/reports.js:24,39` uses `VITE_API_URL` | Every other client uses `VITE_API_BASE_URL` | **Inconsistent** | Silent fallback to hardcoded localhost in any environment where only the "correct" var is set | Standardize on one env var name across the whole frontend |
| Several list GETs omit trailing slash (`admin/candidates`, `admin/interviews`, `admin/strategies`, `admin/interview-modes`, `recruiter/profile`) vs backend routes declared with `/` | FastAPI 307-redirects | **Works, but fragile** | Extra round trip; 307 can drop auth headers in some cross-origin/credentialed configurations | Align trailing slashes everywhere |
| `Team.jsx` compares `status === "Active"` (capitalized) | Backend always returns lowercase `"active"` | **No** | "Active" stat card and status dot always show 0/offline | Fix the frontend string comparison |
| Candidate Settings page — 5 of 7 field names | Backend `SettingsUpdateRequest` schema | **No** | Toggles silently no-op | Rename frontend fields to match backend exactly (§6, §7) |
| `GET /api/auth/profile` returns hardcoded `name`/`email` regardless of token | — | **No** (backend stub, not a frontend bug) | Any caller gets wrong data | Implement real profile lookup as the docstring already describes |

All other audited frontend↔backend pairs (full list in the dedicated agent reports — Auth, Admin companies/recruiters/reports/users/system/settings, Company analytics/campaigns/jobs/exports/profile/dashboard/team sub-resources, Candidate portal, interview/WS/STT/TTS, recruiter profile) matched exactly on path and were confirmed not to have field-name mismatches beyond what's listed above.

---

## 11. Database / Persistence Audit

- **Actively written collections** (confirmed via `collection_name` across all live repositories): `activity_log, audit_logs, interview_campaigns, candidates, candidate_settings, candidate_workflows, company_notifications, companies, exports, interview_mode_definitions, interview_reports, interview_sessions, interview_turns, candidate_invitations, candidate_notifications, platform_settings, recruiters, reports, resume_analyses, security_logs, strategies, support_tickets, users, validator_logs, job_openings, admin_notifications`.
- `create_indexes()` confirmed wired into `main.py` lifespan (runs after `connect_db()`, before `bootstrap_platform()`), ~27 indexes, all guarded against re-run failures.
- **`InterviewSessionSchema` full round-trip confirmed**: `ai_interview/persistence/repository.py` uses `model_dump(mode="json")` / `model_validate(doc)` — every schema field persists and loads correctly; no partial-field mismatch found.
- **Two session repositories are both live, not duplicates**: `app/repositories/interview_session_repository.py` (simple CRUD, no-arg constructor, used by ~20 admin/company read paths) vs `app/ai_interview/persistence/repository.py` (OCC + fencing + idempotency, explicit collection arg, used by the live interview engine). Both bind the same `interview_sessions` collection but serve genuinely different concerns — **keep both**.
- **Confirmed dead, by proof of zero imports**: `db/models.py`'s duplicate `ValidatorLog` class definitions (lines 480 and 493 — Python silently keeps only the second; neither is ever imported from `app.db.models` anywhere); `InterviewSession`/`InterviewTurn`/`InterviewReport` classes in `db/models.py` (the live versions are the `*Schema` classes under `ai_interview/schemas/`).

---

## 12. AI Interview Engine Audit

(Full detail already in §6; this section adds the items not captured in the compliance matrix.)

**Confirmed architecturally sound and spec-compliant:**
- Strategy snapshot immutability, versioning, 16-combination registry, priority formula, evidence enums, claim-vs-proof separation, practice/official isolation, voice snapshotting.

**Confirmed gaps requiring new work (not rewrites):**
1. **Situational/Case is non-functional end-to-end.** Prompt templates exist (`D.situational`, `ENV.situational`, 5 category blocks) but `scenario_context` is hardcoded `None` in `question_turn_planner.py:198,244`, and `blueprint_planning/` never tags any topic with `dimension=situational`. **Required work:** add a scenario bank (data source) and a situational-topic-selection step to blueprint planning; thread `scenario_context` through to `QuestionRequestBuilder`.
2. **Budget cross-validation rule is missing.** Spec: `max_questions_per_topic × count(critical_topics)` should not exceed `max_questions` (warn, don't block). **Required work:** add a `@model_validator` or post-save check in `StrategyDefinition`/campaign creation that raises a warning (not necessarily a hard error) when this is violated.
3. **Evidence model doesn't reach the report.** See §6, §17 — this is the single highest-value fix for architecture compliance.
4. **`ShadowPriorityCalculator` naming is misleading** — it is genuinely live/authoritative. Low-priority rename for code clarity only.

---

## 13. Prompt Library Audit

All 16 combinations (AD_TECH, AD_MIXED, FC_TECH, FC_RESUME, FC_BEHAV, FC_SIT, FC_MIXED, CS_TECH, BS_TECH, BS_RESUME, BS_BEHAV, BS_SIT, BS_MIXED, GV_TECH, GV_MIXED, BA_HR) are present in `registry.py` exactly as the Prompt Library document specifies, in the same order, with matching `allowed_categories` per combination. Block assembly order (`M0_COMMON + S.* + D.* + ENV.* + C.*.* + ADD.* + OUTPUT_CONTRACT`) matches `resolver.py:97-106` exactly. `CONTEXT_META` is absent — this is a stricter-than-spec choice (spec defaults it off anyway) and requires no action. The only functional gap is the Situational dimension's dead `scenario_context` input (see §12 item 1) — the prompt text itself is fully built and correct; only the upstream data source is missing.

---

## 14. Practice Mode Audit

- Question count: **exactly 3, confirmed correct** (`total_question_budget=3, min_questions=3, max_questions=3`).
- Topic wording: **two conflicting hardcoded sources**, neither matching the specified wording:
  - `session_creation_service.py:179,189,199` (cosmetic `topic_name`, never shown to candidate)
  - `question_engine.py:136-146` (actual delivered text: "Tell me about yourself.", "What is the last project you worked on?", "What role or area are you specifically strongest in?")
  - Neither says "Introduction and Background" / "Recent Experience and Work" / "Proudest Project or Contribution" verbatim.
- Isolation from official engine: **fully confirmed** via explicit `mode_id == "practice"` branches in completion, topic selection, follow-up policy, evaluation/evidence pipeline, adaptive difficulty, and blueprint topic selection.
- Campaign voice applies to practice: **confirmed**, unconditional snapshot read.
- **Confirmed broken:** `useCompletePractice` hook is imported and destructured in `InterviewRoom.jsx` but **never invoked** — the REST `POST /api/candidate/practice/complete` call (which flips the candidate workflow stage to `OFFICIAL_INTERVIEW_READY`) never fires. Completion is only inferred client-side from the WS `interview_completed` event, meaning the candidate dashboard's "Practice completed" checklist item may never update correctly.

---

## 15. Voice / STT / TTS Audit

- Allowlist `{shubh, simran, rohan, ishita, sunny}` confirmed identical across 5 independent hardcoded declarations (`schemas/company.py:7`, `api/interview.py:433`, `api/company/campaigns.py:59,317`, `api/company/platform_config.py:40`). No trace of `ritu`/`manan` anywhere.
- Session voice snapshot confirmed (`ai_interview/schemas/session.py:86`, populated at `session_initializer.py:129`).
- Running-session stability confirmed: TTS endpoint (`api/interview.py:437-458`) always prefers `session.voice_id` over a live campaign re-fetch; campaign fallback only applies to legacy/unsnapshotted sessions.
- STT: Sarvam Saaras adapter, REST endpoint (not WebSocket), resilience policy with exponential backoff, fatal/transient error classification.
- TTS: Sarvam Bulbul adapter, same pattern.
- **Gap:** the 5 hardcoded voice-allowlist declarations should be consolidated into one shared constant to eliminate drift risk (currently consistent, but fragile).

---

## 16. Campaign / Strategy Audit

- Campaign creation/editing field-by-field comparison confirmed correct for: interview type, mixed composition, strategy_id, budget override, language, voice, requirements.
- **Confirmed bug:** the Difficulty dropdown offers an "Adaptive" option (`NewCampaign.jsx:493-497`, `EditCampaign.jsx:552-557`) that is **not a member of the backend's `DifficultyLevel` enum** (`easy|medium|hard` only). Selecting it causes a Pydantic 422 on submit, with no frontend indication the option is invalid.
- Strategy management: backend fully built (CRUD, versioning, activation) but **no admin UI exists to author or edit a `StrategyDefinition`**. Three disconnected "strategy" surfaces exist in the admin UI: (1) a dead `SettingsAPI.getStrategies` call, never invoked; (2) `CompanyWizard/StrategiesTab.jsx`, which only toggles which already-existing strategies a company may use (not CRUD); (3) `PlatformSettings.jsx`'s "Strategies" tab, 4 cosmetic toggles with no relation to real `strategy_id`s.

---

## 17. Evidence / Evaluation Audit

Confirmed field-by-field threading:

| Hop | File | Status |
|---|---|---|
| Enums declared | `core/enums.py` — `ResumeEvidence{ABSENT,PARTIAL,STRONG}`, `InterviewEvidence{NOT_DEMONSTRATED,BASIC,ACCEPTABLE,STRONG}` | ✅ |
| TopicProgress | `schemas/session.py:52-55` | ✅ declared + populated (`session_initializer.py:78` for resume_evidence; `evaluation_applicator.py:46-49` for the other two) |
| EvaluationRecord | `answer_engine/schemas.py:50-51,66-67,87-88` | ✅ declared + populated |
| **InterviewResultService** | `services/interview_result_service.py` | ❌ **never read** — output dict keys are `session_id, status, has_report, overall_score, question_count, completed_at, question_feedback, topic_scores, strengths, weaknesses, improvement_suggestions, company_remarks` — none of the three evidence fields appear |

Claim-vs-proof separation (the specific "I know Docker" test case) is **correctly enforced** — no code path converts `candidate_claim` text into `interview_evidence` without a real LLM evaluation call.

---

## 18. Reporting / PDF Audit

**PDF generation is non-functional everywhere it appears to exist:**

| Endpoint | Actual behavior |
|---|---|
| `POST /admin/reports/export/pdf` | Returns a hardcoded, invalid dummy PDF byte string (`reports_service.py:197-199`) |
| `POST /admin/reports/export/csv` | **Real** — builds an actual CSV from live data |
| `GET /company/exports/download/{id}` | Always builds plain-text content regardless of stored format; just swaps the `Content-Type` header |
| `POST /company/exports` | Never generates a file; fabricates a fake `size` string, stores metadata only |
| `GET /company/reports/download/{id}` | Same plaintext-mislabeled-as-PDF pattern |
| `POST /company/reports` | Same fabricated-metadata pattern |

`app/reports/report_generator.py`, `pdf_renderer.py`, and **both HTML templates under `app/reports/templates/`** are confirmed 0 bytes — there was never a working implementation, not even a partially-finished one. `weasyprint`/`Jinja2` are pinned in `requirements.txt` but never imported anywhere in `app/`.

Frontend "Download PDF" buttons: some are wired to the above stubs (admin Reports, company Exports/Reports — will download fake/mislabeled files), others have no handler at all (`AIReports.jsx`, `CandidateReport.jsx`, candidate `Reports.jsx` — clicking does nothing).

**The candidate/company-facing JSON report itself (not PDF) is real and data-driven** — `interview_result_service.py` was deliberately rewritten to remove hardcoded mock fields (confirmed via code comments and a dedicated test asserting a `BANNED_FIELDS` list is absent). Its only gap is the missing evidence model (§17), not fabrication.

---

## 19. Analytics / Explainability Audit

- `CompletionDecisionTrace`, `FollowUpDecisionTrace`, `DifficultyDecisionTrace` are computed internally for every decision but **never surfaced in any UI** — they exist purely as structured log output today.
- Admin Analytics page is **100% mock data**, despite a fully-wired `AnalyticsAPI` client sitting unused.
- Company analytics (`company/analytics.py`, 7 endpoints) are real, connected, and match field-for-field with `analyticsService.js` — this half of the system works correctly.
- `ai_center_service.py`/`ai_reports_service.py` have several fields explicitly hardcoded to `0` (e.g. `average_interview_score`, `technical_score`) with comments acknowledging the aggregation isn't wired up yet.

---

## 20. Authentication / Authorization Audit

- Login: fully functional, tested (backend only).
- Register: does not exist (not a bug — feature was simply never built; confirm whether it's in scope).
- Refresh: **dead end-to-end**. Server generates and stores a real hashed refresh token; `POST /api/auth/refresh` ignores all input and always returns the literal string `"new_token_here"`; no frontend code ever calls this endpoint; no 401-retry interceptor exists. A user is simply logged out when their short-lived access JWT expires.
- Logout: server-side no-op (comment: "Clear refresh token from DB logic can go here"); only the admin `UserMenu.jsx` actually calls the backend endpoint (and silently swallows failures); every other role's logout button only clears `localStorage`.
- **Confirmed bug:** JWT payload never includes `name`/`email` claims, but `AuthContext.jsx:59-61,182-184` reads `decoded.name`/`decoded.email` — these are **permanently empty strings** for every user, everywhere in the app that relies on the auth context (not a separate profile fetch) for display name/email.
- RBAC: two independent layers (`UserRole` + `require_role` for the primary 4 roles; `SubRole`/`Permission` matrix for company team members) — loosely connected, permission lookups currently fall back to role-string matching rather than real JWT sub-role claims.
- `GET /api/auth/profile`: admin-only, returns hardcoded `name`/`email` regardless of actual token, despite a comment describing the intended real implementation.

---

## 21. Payment Boundary Audit

**Scope: boundary only, per instructions — no redesign proposed.**

- No real payment gateway exists anywhere (`grep` for Razorpay/Stripe/PayPal/PayU/Cashfree across the whole repo returns zero hits).
- `IntelliHirePaymentProvider.verify_payment()` (`payment_service.py`) unconditionally returns `True` — no signature/HMAC check, no webhook.
- `PaymentGateway.jsx` is an explicitly-labeled simulator (UI text: *"Secure Simulated Payment"*, *"This is a simulated payment gateway. No real money will be charged."*) — pure `setTimeout` choreography generating a fake payment ID; entered card/UPI details are never transmitted anywhere.
- Pricing (`subscription_pricing_service.py`) and expiry scheduling (`subscription_expiry_service.py`) are real, deterministic business logic — not mocked.
- **Confirmed functional bug (adjacent to, not part of, the payment simulation):** `changeSubscription`/`verifyChangePayment` wrapper functions in `api/subscription.js:11-18` are called with extra arguments (`allowedLanguages, allowedVoices, allowedLlmTiers, allowedInterviewModes`) that the function signatures don't declare — these are silently dropped, so a company's AI-config changes made during a subscription upgrade/downgrade are never persisted.
- **Test coverage: zero** — no test file anywhere references "payment".

This audit does not recommend replacing the simulator; that is a separate, larger decision outside the interview-engine scope per the task's own instructions. The one concrete bug (dropped config fields) is listed in §25/§26 as a small, isolated fix.

---

## 22. Dead / Legacy / Duplicate Code Audit

Every item below was checked by import/route/consumer search before classification — nothing here is "looks old" reasoning.

| Component | Consumers | Live? | Replaced by | Tested? | Recommendation |
|---|---|---|---|---|---|
| `app/resume_processing/{parser,cleaner}.py` | `resume_processing_service.py` → `candidate_portal.py` | **YES** | Not replaced — distinct from the AI-interview resume pipeline, serves candidate-portal upload | No dedicated test | **KEEP** |
| `app/ai_interview/resume_processing/*` | blueprint_planning, question_engine, session_initializer, transport | **YES** — different feature (interview context, not portal upload) | N/A, coexists | 7 dedicated test files | **KEEP** |
| `app/speech/sarvam_client.py` | none | NO (0 bytes) | `ai_interview/speech_infrastructure/{stt,tts}/sarvam_*_adapter.py` | No | **DELETE** |
| `app/analytics/{aggregation,dashboard_service,metrics}.py` | none | NO (0 bytes) | `app/services/{analytics_service,dashboard_service}.py` | No | **DELETE** |
| `app/reports/report_generator.py`, `pdf_renderer.py`, both `templates/*.html` | none | NO (all 0 bytes) | Nothing real exists (§18) | No | **DELETE** (or: implement for real, see §26 R-04) |
| `app/validation/question_validator.py` | none | NO (0 bytes) | `app/ai_interview/question_engine/question_validator.py` | No | **DELETE** |
| `app/middleware/error_handler.py` | none | NO | `app/middleware/exception_handlers.py` (the one actually wired into `main.py`) | No | **DELETE** |
| `app/api/admin_proxy.py` | **Not registered in `main.py` at all** (confirmed — no `include_router(admin_proxy...)` line exists); zero frontend calls to `/api/admin/*` | NO | `app/api/admin/*.py` (different path prefix, `/admin/...`) | No | **DELETE** |
| `app/api/company/recruiters.py` (prefix `/recruiters`, not `/company/recruiters`) | Zero frontend calls found | NO | `app/api/company/team.py` | No | **DELETE AFTER MIGRATION-CHECK** (confirm no external Postman/API consumer depends on it) |
| `db/models.py` duplicate `ValidatorLog` (lines 480, 493) | Neither imported anywhere | NO | N/A — dead regardless | No | **DELETE** both; repository uses raw dicts |
| `db/models.py` `InterviewSession`/`InterviewTurn`/`InterviewReport` classes | Never imported (only `Strategy, Payment, SubscriptionHistory, User, AuditLog, JobOpening, CompanySubscription` are ever imported from `db/models.py`) | NO | `ai_interview/schemas/{session,turn,report}.py` | No (the schema versions are tested) | **DELETE** |
| `pages/candidate/{ResumeUpload,InterviewSetup,ReportView,Registration}.jsx` | Not imported by any route | NO | `Resume.jsx`, `InterviewRoom.jsx`, `Reports.jsx` | No | **DELETE** |
| `pages/recruiter/ChangePassword.jsx` | Not imported anywhere (`App.jsx` uses the company one) | NO | `pages/company/ChangePassword.jsx` | No | **DELETE** |
| `routes/CompanyRoutes.jsx` | Not imported | NO | Inline routes in `App.jsx` | No | **DELETE** |
| `components/recruiter/` (empty dir) | — | NO | — | — | **DELETE** (empty directory) |
| `frontend/test-payment.jsx`, `test-ssr.jsx` | Not part of the Vite build, manual debug scripts outside `src/` | NO (dev scratch files) | — | — | **DELETE** or move to a `scripts/`/`dev-tools/` folder outside `src/` |
| `app/api/company/jobs.py` recruiter access | `require_role(COMPANY)` only — no recruiter access, unlike every other company module | — | — | — | **DEFER** — confirm intentional before changing |
| Two API client styles (`src/api/*.js` fetch vs `src/services/**/*.js` axios) | Both actively used by different feature areas | **YES, both** | — | — | **REFACTOR** (not delete) — consolidate onto one client over time; both are currently load-bearing |

**Explicitly NOT duplicates (confirmed live, keep both):**
- `app/repositories/interview_session_repository.py` vs `app/ai_interview/persistence/repository.py` — different concerns (simple read CRUD vs OCC-protected transactional engine repo).
- `app/resume_processing/*` vs `app/ai_interview/resume_processing/*` — different features (portal upload vs interview-context extraction).
- `pages/company/Recruiters.jsx` vs `pages/company/Team.jsx` — both live, but genuinely redundant UI hitting the same backend with inconsistent feature sets; this is a **consolidation** candidate, not a delete-one-keep-other candidate, since each has UI capabilities the other lacks (see §26 R-07).

---

## 23. Files Recommended for Deletion

(Repeating the DELETE rows from §22 as a single actionable list, each with its proof already stated above.)

1. `backend/app/speech/sarvam_client.py`
2. `backend/app/analytics/aggregation.py`, `dashboard_service.py`, `metrics.py`
3. `backend/app/reports/report_generator.py`, `pdf_renderer.py`, `templates/report_template.html`, `templates/dashboard_export_template.html` (unless §26 R-04 is chosen instead — implement rather than delete)
4. `backend/app/validation/question_validator.py`
5. `backend/app/middleware/error_handler.py`
6. `backend/app/api/admin_proxy.py`
7. `backend/app/api/company/recruiters.py` (after a migration-check confirming no external consumer)
8. `backend/app/db/models.py` — the duplicate `ValidatorLog` definitions and the unused `InterviewSession`/`InterviewTurn`/`InterviewReport` classes (partial-file edit, not whole-file deletion)
9. `frontend/src/pages/candidate/ResumeUpload.jsx`, `InterviewSetup.jsx`, `ReportView.jsx`, `Registration.jsx`
10. `frontend/src/pages/recruiter/ChangePassword.jsx`
11. `frontend/src/routes/CompanyRoutes.jsx`
12. `frontend/src/components/recruiter/` (empty directory)
13. `frontend/test-payment.jsx`, `frontend/test-ssr.jsx` (or relocate outside `src/`)

**Every deletion above must be preceded by a full test run and a final grep confirmation at delete-time** — this audit is a point-in-time snapshot; re-verify immediately before deleting (§30).

---

## 24. Files That Must NOT Be Deleted

- `app/resume_processing/{parser,cleaner}.py` — live, feeds candidate portal uploads.
- `app/ai_interview/resume_processing/*` — live, feeds interview blueprint context.
- `app/repositories/interview_session_repository.py` — live, used by ~20 admin/company read paths.
- `app/ai_interview/persistence/repository.py` — live, the transactional engine repo.
- `app/api/company/jobs.py`, all other company/admin/recruiter routers not explicitly listed in §23.
- `pages/company/Recruiters.jsx` and `Team.jsx` — both live; consolidate, don't delete either outright, until feature parity is confirmed and migrated.
- Anything under `backend/tests/` or `frontend/src/**/*.test.*`.
- `requirements.txt` entries for `weasyprint`/`Jinja2` — keep if §26 R-04 (implement real PDF generation) is chosen; only remove if PDF export is deliberately descoped.
- Both `src/api/*.js` and `src/services/**/*.js` — both are currently load-bearing; this is a REFACTOR target, not a DELETE target (see §22).

---

## 25. Remaining Work

Every item has ID, Title, Area, Description, Why, Current state, Files, Dependencies, Risk, Tests required, Acceptance criteria, Priority.

### R-01 — Thread evidence model into InterviewResultService
- **Area:** AI Interview Engine / Reporting
- **Description:** Add `resume_evidence`, `candidate_claim`, `interview_evidence` (per topic) and a per-topic `final_assessment` enum to the report output.
- **Why:** Architecture doc §16 requires an explainable report; currently 0% of the evidence model reaches any consumer.
- **Current state:** Fields fully populated in `TopicProgress`/`EvaluationRecord`, dropped at `interview_result_service.py`.
- **Files:** `backend/app/services/interview_result_service.py`, possibly `backend/app/schemas/candidate_portal.py` (reconcile the stale `ReportResponse` schema — see R-02).
- **Dependencies:** None — purely additive.
- **Risk:** Low — read-only aggregation change, no behavior change to the interview itself.
- **Tests required:** Extend `test_interview_result_service.py` to assert evidence fields appear; extend `test_interview_report_endpoint.py`'s `BANNED_FIELDS` pattern to also assert REQUIRED fields are present.
- **Acceptance criteria:** A completed session's report includes, per topic: `resume_evidence`, `candidate_claim`, `interview_evidence`, `final_assessment`, `questions_asked[]`, `followup_depth`, `followup_categories_used[]`, `skip_reason` (where applicable), plus a session-level requirement-coverage summary.
- **Priority:** P0

### R-02 — Reconcile stale `ReportResponse` schema
- **Area:** Backend schemas
- **Description:** `schemas/candidate_portal.py`'s `ReportResponse` (fields: `technical_score, communication_score, confidence,` etc.) does not match what `interview_result_service.py` actually returns or what the frontend actually reads (`topic_scores`, `score_100`, `coverage_signal`).
- **Why:** A stale declared contract invites future bugs; the frontend works today only because it was written against the real service output, not the schema.
- **Current state:** Schema exists but is effectively dead/misleading.
- **Files:** `backend/app/schemas/candidate_portal.py`, `backend/app/api/interview.py:116`.
- **Dependencies:** R-01 (do this after evidence fields are finalized, so the schema is written once against the final shape).
- **Risk:** Low if done after R-01.
- **Tests required:** A schema-conformance test asserting the actual endpoint response validates against the declared Pydantic model.
- **Acceptance criteria:** `ReportResponse` accurately describes the live endpoint's output; frontend requires no changes since it already reads the correct fields.
- **Priority:** P1

### R-03 — Build Situational/Case topic + scenario source
- **Area:** AI Interview Engine / blueprint_planning
- **Description:** Add a scenario bank and situational-topic-selection step so `dimension=situational` topics can actually be produced, and thread real `scenario_context` through to `question_turn_planner.py`.
- **Why:** One of the 5 architecture-mandated interview types is currently non-functional; FC_SIT/BS_SIT prompt combinations can never fire with real content.
- **Current state:** Prompt templates fully built; data source entirely absent.
- **Files:** `backend/app/ai_interview/blueprint_planning/*` (new scenario source + topic_selector change), `backend/app/ai_interview/question_engine/question_turn_planner.py:198,244`.
- **Dependencies:** None technically, but needs a product decision on where scenario content comes from (role-derived bank — static seed data vs. admin-authored).
- **Risk:** Medium — touches blueprint planning, a core deterministic component; must not regress Technical/Resume/Behavioral/Mixed paths.
- **Tests required:** New blueprint_planning tests for situational topic generation; new question_engine tests confirming `scenario_context` is populated and FC_SIT/BS_SIT prompts render real content (no `NOT_PROVIDED`).
- **Acceptance criteria:** A campaign configured with Situational or Mixed (with situational weight > 0) produces at least one real situational question referencing actual `scenario_context`, not `NOT_PROVIDED`.
- **Priority:** P1

### R-04 — Decide and implement real PDF generation (or formally descope)
- **Area:** Reporting
- **Description:** Either implement real WeasyPrint/Jinja2-based PDF rendering using the existing (currently empty) template files, or formally remove the dead code and disable the UI buttons that call it.
- **Why:** Every "Download PDF" surface in the product either downloads fake content or does nothing — this is a visible, demo-breaking gap.
- **Current state:** 100% non-functional; dependencies installed but unused.
- **Files:** `backend/app/reports/{report_generator,pdf_renderer}.py`, `templates/*.html`, `backend/app/services/reports_service.py:197-199`, `backend/app/api/company/exports.py`, `backend/app/api/company/reports.py`.
- **Dependencies:** R-01 if the PDF should include the evidence-aware report content.
- **Risk:** Medium — WeasyPrint has native dependencies (Pango/Cairo/GDK-Pixbuf) that can complicate clean installs, especially on Windows; verify the install story before committing to this path.
- **Tests required:** New endpoint tests asserting a valid, parseable PDF (not dummy bytes) is returned; content-type matches actual content.
- **Acceptance criteria:** Clicking "Download PDF" anywhere in the product either produces a real, correctly-labeled PDF, or the button is removed/disabled with an honest "coming soon" state.
- **Priority:** P1 (demo-visible) — but this is the kind of task that should get an explicit go/no-go decision from the user given the WeasyPrint install risk; see §34.

### R-05 — Fix Candidate Settings field-name mismatches
- **Area:** Frontend / Candidate
- **Description:** Rename 5 frontend field keys to match the backend schema exactly.
- **Why:** Most of the Settings page silently does nothing today.
- **Current state:** Broken.
- **Files:** `frontend/src/pages/candidate/Settings.jsx` (lines ~102,117,127,153-154,168).
- **Dependencies:** None.
- **Risk:** Very low — pure rename, no backend change needed.
- **Tests required:** A new frontend test (or at minimum manual verification) confirming each toggle persists and reloads correctly.
- **Acceptance criteria:** All 7 Settings toggles read and write correctly round-trip through the backend.
- **Priority:** P1 (small, isolated, high confidence fix — good first task)

### R-06 — Fix Company candidate-service missing/broken methods
- **Area:** Frontend / Company
- **Description:** Add `suspendCandidate`, `activateCandidate`, `resetCredentials`, `inviteCandidate`, `bulkAssignCandidates` to `candidateService.js`; fix or remove `sendInvite`/`downloadResume`/`downloadReport` (currently call non-existent backend routes).
- **Why:** The entire "Add Candidate"/suspend/activate/invite flow in the Company Candidates page is currently broken (throws `TypeError` before even reaching the network).
- **Current state:** Broken — confirmed via direct code read on both sides.
- **Files:** `frontend/src/services/company/candidateService.js`, `frontend/src/pages/company/Candidates.jsx`, `CandidateDetails.jsx`.
- **Dependencies:** None for the 5 missing-method fixes; for `sendInvite`/`downloadResume`/`downloadReport`, decide whether to add the missing backend routes or repoint to existing ones.
- **Risk:** Low for the 5 missing methods (backend already supports them); medium for the 3 need-new-route items (new backend surface).
- **Tests required:** New frontend tests or at minimum integration smoke tests for each action.
- **Acceptance criteria:** Every button in Candidates.jsx/CandidateDetails.jsx performs its stated action successfully.
- **Priority:** P1

### R-07 — Consolidate Recruiters.jsx and Team.jsx
- **Area:** Frontend / Company
- **Description:** Merge the two duplicate recruiter-management pages/services into one, keeping the union of both feature sets (Recruiters.jsx has suspend/activate/force-reset/campaign-assignment/activity drawer; Team.jsx has a simpler invite/remove flow).
- **Why:** Confusing duplicate UI/UX, double maintenance burden, and the status-casing bug (R-08) only affects one of the two.
- **Current state:** Both live, both hit `/company/team`.
- **Files:** `frontend/src/pages/company/{Recruiters,Team}.jsx`, `frontend/src/services/company/{recruiterManagementService,teamService}.js`.
- **Dependencies:** R-08 (fix the casing bug as part of this consolidation).
- **Risk:** Medium — must preserve all currently-working functionality from both pages during merge.
- **Tests required:** New tests covering the merged page's full feature set.
- **Acceptance criteria:** One page, one service, all prior functionality preserved, status display correct.
- **Priority:** P2

### R-08 — Fix Team.jsx status-casing bug
- **Area:** Frontend / Company
- **Description:** `Team.jsx` compares `status === "Active"` (capitalized); backend always returns lowercase `"active"`.
- **Why:** The "Active" stat card and status dot always show 0/offline regardless of real state.
- **Current state:** Broken.
- **Files:** `frontend/src/pages/company/Team.jsx:67,212`.
- **Dependencies:** None (can be done standalone, or folded into R-07).
- **Risk:** Very low.
- **Tests required:** Manual/visual confirmation after fix.
- **Acceptance criteria:** Active recruiter count and status dots display correctly.
- **Priority:** P1 (trivial, high-value fix — good first task alternative to R-05)

### R-09 — Fix Campaign "Adaptive" difficulty option
- **Area:** Frontend+Backend / Company Campaigns
- **Description:** Either remove "Adaptive" from the difficulty dropdown, or add it as a valid `DifficultyLevel` enum member with real backend behavior.
- **Why:** Selecting it currently causes a silent-to-the-user 422 on campaign submit.
- **Current state:** Broken.
- **Files:** `frontend/src/pages/company/{NewCampaign,EditCampaign}.jsx`, `backend/app/ai_interview/core/enums.py:31-34` (if adding support instead of removing the option).
- **Dependencies:** Product decision: is "Adaptive" a meaningful difficulty band, or was it meant to describe the *strategy* (Adaptive Depth), not a literal difficulty level? Likely the latter, given the architecture doc's actual adaptive-difficulty design (§6) is per-topic and automatic, not a campaign-selectable "difficulty".
- **Risk:** Low if removing; the dropdown bug is a one-line fix either way.
- **Tests required:** Campaign creation/edit smoke test with each valid difficulty value.
- **Acceptance criteria:** No invalid difficulty option can be submitted; backend enum and frontend dropdown are in sync.
- **Priority:** P1

### R-10 — Build Admin Strategy authoring UI
- **Area:** Frontend / Admin
- **Description:** Build a real admin page for creating, editing, versioning, and activating `StrategyDefinition`s against the existing, fully-built backend CRUD+versioning API.
- **Why:** This is the single largest Frontend↔Backend gap in the entire audit — a fully-built, tested backend feature has zero usable UI. Today an admin must use Swagger/Postman to manage strategies.
- **Current state:** Backend 100% complete; frontend 0% (three disconnected, non-functional "strategy" surfaces exist, none of which can author a real strategy).
- **Files (new):** `frontend/src/pages/admin/Strategies.jsx`, `StrategyDetail.jsx`, `NewStrategy.jsx`/`EditStrategy.jsx`; `frontend/src/api/strategies.js` (new, dedicated client — the existing dead `SettingsAPI.getStrategies` can be retired into this).
- **Dependencies:** None — this is purely additive to existing, stable backend endpoints.
- **Risk:** Low to the rest of the system (new page, no existing code touched beyond adding a route and a nav link) but requires careful form design given `StrategyDefinition`'s nested policy objects (`difficulty_policy`, `followup_policy`, `gap_policy`, `completion_policy`, `company_override_bounds`).
- **Tests required:** New frontend tests for the create/edit/version/activate flows; smoke test against the real backend endpoints.
- **Acceptance criteria:** An admin can create a new strategy, create a new version of an existing strategy, and activate/deactivate a specific version, entirely through the UI — matching §23 of the architecture document's demo-ready definition.
- **Priority:** **P0** — see §34, this is the recommended next task.

### R-11 — Fix dead/incomplete Recruiter self-service surface (product decision required)
- **Area:** Backend+Frontend / Recruiter
- **Description:** Decide whether the 4 dedicated recruiter routers (own campaigns, own candidates with shortlist/reject/invite, own dashboard, own interview list) should get a real frontend, or be formally deprecated in favor of the current model (recruiters use the Company portal with company-scoped data).
- **Why:** Currently dead backend surface area; also two of its own endpoints (`POST /candidates/`, `POST /candidates/{id}/send-invite`) have incomplete server-side logic ("Placeholder for credentials generation logic", "Trigger invite email logic here").
- **Current state:** Backend built but unreachable; some of it even internally incomplete.
- **Files:** `backend/app/api/recruiter/*.py`.
- **Dependencies:** Product decision only — no code dependency.
- **Risk:** Low either way, but doing nothing leaves confusing, partially-broken backend surface in place indefinitely.
- **Tests required:** N/A until a direction is chosen.
- **Acceptance criteria:** Either a working recruiter-scoped UI exists, or the routers are documented as intentionally superseded and slated for cleanup.
- **Priority:** P2 (needs a decision, not urgent)

### R-12 — Fix Auth refresh/logout/name-email gaps
- **Area:** Backend+Frontend / Auth
- **Description:** Implement a real `/api/auth/refresh` (validate the stored hashed token, issue a new access token), make `/api/auth/logout` actually revoke the stored refresh token, add `name`/`email` to JWT claims (or fetch them via a real profile call instead of reading from the token), and wire every role's logout button to call the backend.
- **Why:** Sessions currently just die silently on access-token expiry; logout doesn't revoke anything server-side; names/emails are blank everywhere in the UI that relies on the auth context.
- **Current state:** Scaffolded/broken as described in §20.
- **Files:** `backend/app/api/auth.py`, `backend/app/auth/jwt_handler.py`, `backend/app/services/auth_service.py`, `frontend/src/context/AuthContext.jsx`, `frontend/src/api/client.js`, every sidebar/topbar logout button.
- **Dependencies:** None.
- **Risk:** Medium — touches the authentication critical path; must be tested carefully against all 4 roles.
- **Tests required:** New backend tests for refresh (valid/expired/reused token), logout (confirm revocation), and a frontend test confirming `user.name`/`user.email` render correctly after the fix.
- **Acceptance criteria:** An expired access token is silently renewed via refresh without forcing re-login (until the refresh token itself expires); logout actually revokes server-side; name/email display correctly everywhere.
- **Priority:** P2 (not demo-blocking if sessions are short-lived during a demo, but a real correctness gap)

### R-13 — Add budget cross-validation rule
- **Area:** AI Interview Engine / Strategy
- **Description:** Add the spec's `max_questions_per_topic × count(critical_topics) ≤ max_questions` warning check.
- **Why:** Architecture doc explicitly calls this out as a configuration-time safety net ("5 critical skills × 4 questions each = 20 > max 12").
- **Files:** `backend/app/ai_interview/schemas/strategy.py`, `backend/app/ai_interview/blueprint_planning/blueprint_validator.py`, or `backend/app/api/admin/strategies.py` at save time.
- **Dependencies:** None.
- **Risk:** Low — additive validation, should warn not hard-block (per spec).
- **Tests required:** New validator test with an intentionally-overbudget strategy configuration.
- **Acceptance criteria:** Saving a strategy/campaign combination that violates this rule produces a clear warning (not necessarily a blocking error, per spec wording "warn if so").
- **Priority:** P2

### R-14 — API contract fixes (batch)
- **Area:** Frontend
- **Description:** Fix all remaining items in §10's mismatch table not already covered by R-05/R-06/R-09: `PATCH /admin/settings/master` (add route or remove dead call), `GET /company/team/{id}` (add route or filter client-side), trailing-slash alignment, `VITE_API_URL` vs `VITE_API_BASE_URL` env var consistency.
- **Files:** As listed per-row in §10.
- **Dependencies:** None, can be done incrementally, one row at a time.
- **Risk:** Low, each is an isolated fix.
- **Tests required:** Per-fix smoke test.
- **Acceptance criteria:** Zero 404/405 contract mismatches remain in §10's table.
- **Priority:** P2–P3 depending on row (trailing slashes are P3, missing routes are P2)

### R-15 — Fix dropped subscription-change config fields
- **Area:** Frontend / Company Subscription
- **Description:** Add the missing named parameters (`allowed_languages`, `allowed_voices`, `allowed_llm_tiers`, `allowed_interview_modes`) to `changeSubscription`/`verifyChangePayment` in `api/subscription.js`.
- **Files:** `frontend/src/api/subscription.js:11-18`.
- **Dependencies:** None.
- **Risk:** Low.
- **Tests required:** Subscription change flow smoke test confirming AI-config fields persist.
- **Acceptance criteria:** AI-config changes made during a subscription upgrade/downgrade are actually saved.
- **Priority:** P2

---

## 26. Dependency Graph

```
R-01 (evidence→report) ──┬──> R-02 (reconcile ReportResponse schema)
                          └──> R-04 (real PDF, if it should include evidence data)

R-03 (situational topics) ──> (independent; no other item depends on it)

R-05, R-08, R-09, R-13, R-14, R-15 ──> all independent, can run in parallel, any order

R-06 (candidate service fixes) ──> independent

R-07 (Recruiters/Team consolidation) ──depends on──> R-08 (fix casing bug first, as part of or before consolidation)

R-10 (Admin Strategy UI) ──> independent of all AI-engine work; purely additive frontend

R-11 (Recruiter portal decision) ──> independent; blocks nothing, blocked by nothing (pure product decision)

R-12 (Auth refresh/logout/name-email) ──> independent
```

No item in this list requires another to be done first except R-02 after R-01, and R-08 logically preceding/accompanying R-07. Everything else can be sequenced for convenience, not because of a hard technical dependency — this means the roadmap in §27 is ordered by **risk and value**, not by forced dependency chains.

---

## 27. Master Implementation Phases

### PHASE A — Baseline / Safety Net
**Objective:** Establish a safe starting point before any change.
**Tasks:** Confirm current test suite passes (`pytest backend/tests`, `npm test` in frontend if a script exists — currently frontend has no `test` script defined in `package.json`, only `dev`/`build`/`preview`; add one as part of this phase using the existing `vitest` dependency). Tag/commit the current state as the baseline checkpoint.
**Dependencies:** None.
**Output:** A known-good baseline and a working frontend test runner.
**Tests:** Full existing suite green.
**Completion criteria:** Baseline tagged; `npm run test` (new script) runs the 5 existing frontend test files successfully.

### PHASE B — Small, Isolated Bug Fixes (highest confidence, lowest risk)
**Objective:** Fix the concrete, isolated, proven bugs that don't touch architecture.
**Tasks:** R-05, R-08, R-09, R-13, R-14, R-15.
**Dependencies:** Phase A.
**Output:** Candidate Settings works; Team.jsx status displays correctly; campaign difficulty dropdown is valid; budget warning exists; API contract 404s are fixed; subscription config fields persist.
**Tests:** One test per fix, as specified in §25.
**Completion criteria:** All listed bugs verifiably fixed with a passing test or manual confirmation; no regressions in Phase A's baseline suite.

### PHASE C — Candidate/Company Service-Layer Repairs
**Objective:** Restore broken write-paths in the Company Candidates flow.
**Tasks:** R-06.
**Dependencies:** Phase A (not B, can run in parallel with B).
**Output:** Add/Suspend/Activate/Invite/Reset/Bulk-assign all functional.
**Tests:** New service-layer tests + manual flow verification.
**Completion criteria:** Every button in Candidates.jsx/CandidateDetails.jsx performs its intended backend action.

### PHASE D — AI Engine Architecture Compliance (the core of this roadmap)
**Objective:** Close the architecture-document gaps.
**Tasks:** R-01 → R-02 (in order), R-03, R-04 (pending the go/no-go decision in §34).
**Dependencies:** Phase A. Independent of B/C.
**Output:** Evidence-aware reporting; functional Situational interview type; a real decision on PDF generation.
**Tests:** As specified per-task in §25; extend `tests/ai_interview/` and `tests/integration/` accordingly.
**Completion criteria:** §6's compliance matrix P0/P1 rows move to COMPLETE.

### PHASE E — Admin Strategy UI (highest-leverage new feature)
**Objective:** Make the fully-built backend strategy system usable.
**Tasks:** R-10.
**Dependencies:** Phase A only.
**Output:** A working admin strategy authoring/versioning/activation UI.
**Tests:** New frontend tests + end-to-end smoke test against real backend.
**Completion criteria:** An admin can fully manage strategies without Swagger/Postman.

### PHASE F — UI Consolidation & Cleanup
**Objective:** Remove duplication and dead code, now that live flows are confirmed stable.
**Tasks:** R-07; §23's deletion list (re-verified immediately before deletion); §22's REFACTOR item (API client consolidation) started but not necessarily finished here.
**Dependencies:** Phases B, C, D, E should be substantially complete first — cleanup happens last, per the task's own instructions ("cleanup MUST happen only after live flows are confirmed").
**Output:** No dead files remain uncertain; Recruiters/Team consolidated.
**Tests:** Full regression suite after every deletion batch.
**Completion criteria:** §23's list is fully actioned (deleted or explicitly deferred with reason); full test suite still green.

### PHASE G — Auth Hardening
**Objective:** Fix refresh/logout/name-email gaps.
**Tasks:** R-12.
**Dependencies:** Phase A only; can be done any time, placed here because it's not demo-blocking but is a real correctness gap worth closing before considering the project "done."
**Output:** Working session renewal, real logout, correct name/email display.
**Tests:** New backend+frontend auth tests.
**Completion criteria:** A user's session survives access-token expiry via refresh; logout is effective; name/email display correctly.

### PHASE H — Product Decisions Resolved
**Objective:** Close out items that need a human decision, not code.
**Tasks:** R-11 (recruiter portal direction).
**Dependencies:** None technically; can happen any time, but should be resolved before final QA so the demo script (§31) doesn't have to route around an undecided feature.
**Output:** A documented decision and, if "build it," a follow-up set of tasks (not written here, since direction is unknown).
**Completion criteria:** Decision recorded; if "build," new atomic tasks added to this document.

### PHASE I — Final QA / Demo Readiness
**Objective:** Verify the full demo script (§31) end-to-end, across all 4 roles.
**Tasks:** Run the full checklist in §32.
**Dependencies:** Phases B–G substantially complete.
**Output:** A project that can be demonstrated per §31 without hitting any of the bugs catalogued in this document.
**Completion criteria:** §32 checklist fully passes.

---

## 28. Atomic One-Task-at-a-Time Roadmap

Each task below is sized for one implement→test→review→next cycle. IDs are stable references back to §25/§27.

- **Task B-01 — Fix Candidate Settings field names.** (= R-05) Files: `Settings.jsx`. Prerequisites: none. Scope: rename 5 field keys. Tests: manual round-trip per toggle. Must NOT touch: backend schema. 
- **Task B-02 — Fix Team.jsx status casing.** (= R-08, standalone portion) Files: `Team.jsx:67,212`. Prerequisites: none. Scope: lowercase comparison. Tests: visual confirmation. Must NOT touch: `recruiterManagementService.js` (save full consolidation for R-07).
- **Task B-03 — Remove or fix "Adaptive" difficulty option.** (= R-09) Files: `NewCampaign.jsx`, `EditCampaign.jsx`. Prerequisites: product decision (is Adaptive meaningful as a difficulty band?). Scope: dropdown fix only in this task; backend enum change is a separate task if the decision is "add support." Tests: campaign create/edit smoke test. Must NOT touch: `DifficultyLevel` enum unless the decision requires it.
- **Task B-04 — Add budget cross-validation warning.** (= R-13) Files: `strategy.py` or `blueprint_validator.py`. Prerequisites: none. Scope: one new validator method. Tests: new unit test with an overbudget config. Must NOT touch: existing validator logic for min/target/max ordering.
- **Task B-05 — Standardize `VITE_API_BASE_URL` env var usage.** (= part of R-14) Files: `api/reports.js:24,39`. Prerequisites: none. Scope: rename the one divergent env var reference. Tests: manual check that exports still resolve the correct base URL. Must NOT touch: other client files already using the correct var.
- **Task B-06 — Align trailing slashes across list GET endpoints.** (= part of R-14) Files: frontend `api/*.js`/`services/**/*.js` calls listed in §10. Prerequisites: none. Scope: add trailing slash to ~6 call sites. Tests: manual network-tab confirmation of no 307 redirects. Must NOT touch: backend route declarations.
- **Task B-07 — Add missing `PATCH /admin/settings/master` route (or remove dead frontend call).** Prerequisites: product decision on whether master settings should be PATCH-able via this path. Files: `admin/settings.py` (if adding) or `api/settings.js` (if removing). Tests: new endpoint test if added. Must NOT touch: `GET /master`.
- **Task B-08 — Add `GET /company/team/{member_id}` route (or fix `getRecruiter` client-side).** Prerequisites: none. Files: `team.py` or `recruiterManagementService.js`. Tests: new endpoint test if added. Must NOT touch: other team.py routes.
- **Task B-09 — Fix dropped subscription-change config fields.** (= R-15) Files: `api/subscription.js:11-18`. Prerequisites: none. Scope: add 4 named parameters. Tests: subscription change flow smoke test. Must NOT touch: backend `company_subscription.py` (already accepts these fields).
- **Task C-01 — Add missing candidateService methods.** (= R-06, part 1) Files: `candidateService.js`. Prerequisites: none. Scope: add `suspendCandidate`, `activateCandidate`, `resetCredentials`, `inviteCandidate`, `bulkAssignCandidates`. Tests: one smoke test per method. Must NOT touch: backend routes (already exist).
- **Task C-02 — Resolve or remove dead `sendInvite`/`downloadResume`/`downloadReport`.** (= R-06, part 2) Files: `candidateService.js`, possibly new backend routes. Prerequisites: product decision (implement missing routes vs repoint to existing ones). Tests: per-decision. Must NOT touch: working parts of `candidates.py`.
- **Task D-01 — Add evidence fields to InterviewResultService output.** (= R-01) Files: `interview_result_service.py`. Prerequisites: Phase A baseline. Scope: extend `_build_topic_scores`/`_build_question_feedback` to include the 3-way evidence model and `final_assessment`. Tests: extend `test_interview_result_service.py`. Must NOT touch: the evaluation pipeline itself (`answer_engine/*`) — this is a read-only aggregation change.
- **Task D-02 — Reconcile `ReportResponse` schema.** (= R-02) Files: `schemas/candidate_portal.py`. Prerequisites: Task D-01 complete. Tests: schema-conformance test. Must NOT touch: frontend (already correct).
- **Task D-03 — Build situational scenario bank + topic selection.** (= R-03, part 1) Files: new file under `blueprint_planning/`, `topic_selector.py`. Prerequisites: product decision on scenario content source. Tests: new blueprint_planning tests. Must NOT touch: Technical/Resume/Behavioral/Mixed topic selection logic.
- **Task D-04 — Wire `scenario_context` through question_turn_planner.** (= R-03, part 2) Files: `question_turn_planner.py:198,244`. Prerequisites: D-03. Tests: question_engine tests confirming non-None scenario_context for situational topics. Must NOT touch: other dimension handling.
- **Task D-05 — Decide and implement (or formally descope) real PDF generation.** (= R-04) Files: as listed in R-04. Prerequisites: a go/no-go decision (§34) given the WeasyPrint install-risk flag. Tests: endpoint tests for valid PDF output. Must NOT touch: the real, working CSV export (`export_csv`).
- **Task E-01 — Build Admin Strategy list/detail read-only view.** (= R-10, part 1) Files: new `pages/admin/Strategies.jsx`, `StrategyDetail.jsx`, new `api/strategies.js`. Prerequisites: none. Scope: list + view existing strategies and their versions (read-only first). Tests: new frontend tests. Must NOT touch: backend.
- **Task E-02 — Build Admin Strategy create/edit form.** (= R-10, part 2) Files: new `NewStrategy.jsx`/`EditStrategy.jsx`. Prerequisites: E-01. Scope: full `StrategyDefinition` authoring form including nested policy objects. Tests: form validation + submit smoke test against real backend. Must NOT touch: E-01's read views.
- **Task E-03 — Build Admin Strategy version-create/activate actions.** (= R-10, part 3) Files: extend `StrategyDetail.jsx`. Prerequisites: E-01, E-02. Scope: "create new version" and "activate version" buttons wired to the existing backend endpoints. Tests: smoke test for both actions. Must NOT touch: existing version-history backend logic (already correct).
- **Task F-01 — Consolidate Recruiters.jsx and Team.jsx.** (= R-07) Files: both pages + both services. Prerequisites: Phases B/C/D/E substantially done; B-02 completed first. Tests: full feature-parity test suite for the merged page. Must NOT touch: `/company/team` backend (already correct).
- **Task F-02 — Execute §23 deletion list.** Files: as listed. Prerequisites: re-verify each file's zero-import status immediately before deleting (do not trust this document's point-in-time snapshot blindly). Tests: full regression suite after each deletion batch. Must NOT touch: anything in §24's protected list.
- **Task G-01 — Implement real `/api/auth/refresh`.** (= R-12, part 1) Files: `auth.py`, `auth_service.py`. Prerequisites: none. Tests: new refresh-flow tests (valid, expired, reused token). Must NOT touch: login flow.
- **Task G-02 — Implement real server-side logout (token revocation).** (= R-12, part 2) Files: `auth.py`. Prerequisites: none. Tests: logout-then-refresh-attempt test confirming the revoked token is rejected. Must NOT touch: G-01's refresh logic beyond the revocation check.
- **Task G-03 — Add name/email to JWT claims (or fetch via real profile call).** (= R-12, part 3) Files: `jwt_handler.py`, `AuthContext.jsx`. Prerequisites: product decision (JWT claim vs separate profile fetch — JWT claim is simpler but makes tokens slightly larger and stale if the user renames themselves before the token expires; a profile fetch is more correct but adds a network call). Tests: frontend test confirming `user.name`/`user.email` render correctly post-login. Must NOT touch: other JWT claims.
- **Task G-04 — Wire all role logout buttons to call the backend.** (= R-12, part 4) Files: `CandidateSidebar.jsx`, `CandidateTopbar.jsx`, `Sidebar.jsx` (admin), `CompanySidebar.jsx`, `CompanyNavbar.jsx`. Prerequisites: G-02. Tests: manual confirmation each logout button calls the backend and doesn't silently swallow errors. Must NOT touch: `UserMenu.jsx`'s existing working call (just remove its over-broad `catch(e){}`).

---

## 29. Testing Strategy

- **Backend:** pytest + pytest-asyncio against a dedicated `intellihire_test` MongoDB database (already correctly isolated via `conftest.py`). External LLM/speech calls are mocked per-test, not globally — any new task touching `ai_interview/` must add its own mocks following the existing pattern (e.g. `@patch`/`MagicMock` on the Groq/Sarvam adapter boundary), not make real API calls in CI.
- **Frontend:** `vitest` + `@testing-library/react` are installed but **no `test` script exists in `package.json`** — Phase A must add one (`"test": "vitest run"` or similar) before frontend testing can be considered part of the standard workflow. Only 5 test files exist today, all mocking the transport layer entirely (no test exercises the real WS message shapes against the backend's actual Pydantic models) — new WS-related work (R-03, D-03/D-04) should add at least one contract-style test validating frontend-sent/received shapes against the real `ws_commands.py`/`ws_events.py` schemas, not just mocked fixtures.
- **Contract tests:** every new/fixed API route in §25/§26/§28 should get at minimum one request/response shape assertion test — this is the single biggest gap surfaced by this audit (most of the confirmed bugs in §9/§10 would have been caught by a basic contract test).
- **Regression discipline:** run the full existing suite before and after every phase in §27, not just before/after individual tasks, to catch cross-cutting breakage early.

---

## 30. Cleanup Strategy

Cleanup is **Phase F**, not Phase A — it happens only after live flows are confirmed stable (per the task's own instruction and this document's §22 evidence-first approach).

For every proposed deletion in §23:
1. **Re-verify immediately before deleting** — re-run the same import/route/consumer grep this audit used; the codebase may have changed between this audit and the actual cleanup task.
2. **Delete.**
3. **Run the full backend + frontend test suite.**
4. **Commit as its own change** (not bundled with feature work), with a commit message citing this document's finding (e.g. "Remove app/speech/sarvam_client.py — confirmed 0 bytes, zero imports, see specs.md §22").

Never batch an uncertain deletion with a certain one — if in doubt about any single file, defer it rather than delete it alongside confirmed-dead files.

---

## 31. Demo-Ready Definition of Done

A reviewer can perform, without hitting any bug catalogued in this document:

**Admin:** Login → create/edit/version/activate a Strategy (via the new UI from Phase E) → configure/view a company → view real (not mock) analytics → view security logs.

**Company:** Login → create a campaign (valid difficulty options only) → select interview type/strategy/mixed-composition/voice/language → invite a candidate (working invite flow) → view candidate list and status actions (all working) → view a completed interview's evidence-aware report → download a real (or honestly-labeled-as-unavailable) PDF.

**Candidate:** Login → upload resume → see it processed → start Practice (exactly 3 questions, consistent wording, completion properly recorded) → start Official Interview → hear the campaign-selected voice → answer via voice or text → receive adaptive follow-ups → complete the interview (real completion page, not a mock) → view their permitted result, including evidence summary where appropriate.

**System:** Strategy snapshot immutable ✓ (already true) · deterministic decision layer controls the interview ✓ (already true) · LLM only generates wording ✓ (already true) · evidence is preserved end-to-end (requires R-01) · voice is session-stable ✓ (already true) · Mixed composition works ✓ (already true) · completion works ✓ (already true) · reports work (requires R-01, partially true today) · authorization works (mostly true; refresh/logout gaps per R-12) · tests pass (requires Phase A test-script fix for frontend).

---

## 32. Final QA Checklist

- [ ] Frontend builds cleanly (`npm run build`)
- [ ] Frontend has a working `test` script and all tests pass
- [ ] Backend starts cleanly with `.env` placeholder credentials (no real keys required for a basic smoke boot)
- [ ] Backend full test suite passes against `intellihire_test` DB
- [ ] Database: all indexes created without error on a fresh DB
- [ ] Auth: login works for all 4 roles; refresh works (post R-12); logout revokes server-side (post R-12); name/email display correctly (post R-12)
- [ ] Authorization: role guards correctly block cross-role access; recruiter status-suspension is enforced live (already confirmed working)
- [ ] AI Interview — Practice: exactly 3 questions, consistent wording, campaign voice applied, completion properly recorded (post R-14 item in Phase D/C)
- [ ] AI Interview — Official: all 5 interview types produce real questions (Situational post R-03), strategy snapshot immutable, adaptive difficulty/follow-up/completion behave per strategy
- [ ] Voice: allowlist enforced, session-stable across a campaign voice change mid-interview
- [ ] STT: audio successfully transcribed, WAV-conversion fallback works
- [ ] TTS: question audio plays correctly, falls back to browser TTS on failure
- [ ] Campaigns: no invalid difficulty option submittable (post R-09); mixed composition sliders persist correctly
- [ ] Strategies: admin can create/edit/version/activate via UI (post Phase E)
- [ ] Mixed: composition soft-weighting visibly affects topic selection without starving a struggling-topic's priority
- [ ] Evidence: report includes resume/claim/interview evidence per topic (post R-01)
- [ ] Reports: JSON report accurate; PDF either real or honestly unavailable (post R-04 decision)
- [ ] PDF: no endpoint returns fake/mislabeled content (post R-04)
- [ ] Analytics: Admin Analytics page shows real data (post Phase B/task equivalent), Company Analytics already correct
- [ ] Payment boundary: documented as simulated, no real-money risk, config fields persist on change (post R-15)
- [ ] Security: default admin credential rotated/disabled before any shared/production deployment
- [ ] Cleanup: §23 list fully actioned or explicitly deferred with reason, full suite still green
- [ ] Tests: contract tests exist for every newly-fixed API route
- [ ] Build: Docker setup either implemented or explicitly out of scope and documented as such
- [ ] Deployment/demo: the exact script in §31 can be performed start-to-finish without hitting a cataloged bug

---

## 33. Risks / Unknowns / Assumptions

- **NOT VERIFIED:** `HiringAnalytics.jsx`, `Performance.jsx`, `InterviewAnalysis.jsx` (admin) were flagged but not deep-dived by the Admin audit pass — confirm whether they consume real APIs or are also mock-data pages like `Analytics.jsx`.
- **NOT VERIFIED:** `Jobs.jsx`/`JobForm.jsx`, `Interviews.jsx` (company), `RecruiterProfile.jsx`, and the 5 subscription sub-pages (`SubscriptionManagement`, `Payment`, `VerifySubscription`, `RenewSubscription`, `ChangeSubscription`) were sampled only at the service-file level, not the component level, by the Company audit pass.
- **NOT VERIFIED:** `company/exports.py`, `notifications.py`, `audit_logs.py`, `platform_config.py` backend routes and their frontend counterparts were not opened in this pass.
- **ASSUMPTION:** The "Adaptive" difficulty dropdown bug (R-09) is assumed to be a product mix-up between "difficulty level" and "Adaptive Depth strategy" — this should be confirmed with whoever built the campaign UI before deciding whether to remove the option or add backend support for it.
- **ASSUMPTION:** The payment simulator (§21) is assumed to remain a simulator for the current scope, per the task's explicit instruction not to redesign it — if a real gateway is ever required, that is a separate, larger project.
- **RISK:** WeasyPrint's native dependency chain (Pango/Cairo/GDK-Pixbuf) is a known source of clean-install friction, especially on Windows — this is likely *why* PDF generation was never finished, and should be weighed seriously before committing to R-04/D-05's "implement real PDF" path versus the "formally descope" alternative.
- **RISK:** The recruiter-portal direction (R-11) is a product decision this document cannot make — proceeding with cleanup or further backend work on those 4 routers without that decision risks wasted effort in either direction.
- **ASSUMPTION:** "Register" is assumed to be intentionally out of scope (companies/recruiters/candidates are provisioned by admin/company flows, not self-registration) — confirm this is actually the intended product model before treating its absence as a gap rather than a design choice.

---

## 34. Recommended Next Task

**Task E-01 through E-03 — Build the Admin Strategy authoring UI (R-10).**

**Why this is next:**
- It is the single largest, most concrete gap surfaced by this entire audit: a complete, versioned, tested backend feature (`StrategyDefinition` CRUD + version history + activation, all 7 endpoints) with **zero working frontend**, forcing an admin to use Swagger/Postman to configure the core differentiator of the product (the 6 interview strategies).
- It has **no dependency on any other unresolved item** in this document — it doesn't require the evidence-model fix (R-01), the Situational work (R-03), or the PDF decision (R-04). It is purely additive: new pages, one new API client file, zero backend changes, zero risk to the live interview engine.
- It directly unlocks the compliance-matrix status for "Strategy versioning" (§6) moving from "backend complete, UI missing" to fully COMPLETE, and is one of the explicit demo-script steps in §31 ("Admin: ... create/edit/version/activate a Strategy").
- It is safe to start immediately without waiting on any product decision (unlike R-09's difficulty-dropdown ambiguity, R-11's recruiter-portal direction, or R-04's PDF go/no-go).

**What it depends on:** Nothing beyond Phase A (a working baseline). The backend endpoints it will call (`POST /admin/strategies/`, `GET /admin/strategies/`, `GET .../versions`, `POST .../versions`, `PATCH .../versions/{v}/activate`) are already implemented, tested (`test_strategies.py`, `test_strategy_schema.py`), and require no changes.

**What it unlocks:** A genuinely demo-able admin strategy workflow; removes the need for direct API access to manage the product's core configuration; closes the largest Frontend↔Backend gap found in this audit; gives the team confidence to later connect `CompanyWizard/StrategiesTab.jsx`'s company-side "allowed strategies" picker to a real, admin-curated list rather than whatever happens to exist in the DB today.

**Files it will likely touch:**
- New: `frontend/src/pages/admin/Strategies.jsx`, `StrategyDetail.jsx`, `NewStrategy.jsx`, `EditStrategy.jsx`
- New: `frontend/src/api/strategies.js` (retiring the dead `SettingsAPI.getStrategies` call from `settings.js` into this dedicated client)
- Modified: `frontend/src/routes/AdminRoutes.jsx` (add the new routes), `frontend/src/components/admin/Sidebar.jsx` (add a nav entry)

**What must NOT be touched:**
- `backend/app/api/admin/strategies.py` and its schemas — already correct, no backend change required.
- `CompanyWizard/StrategiesTab.jsx` — leave its current "allowed-strategies toggle" behavior as-is for now; connecting it to a richer admin-curated list is a follow-up, not part of this task.
- `PlatformSettings.jsx`'s cosmetic "Strategies" tab — out of scope for this task; it is a separate, lower-priority cleanup item (could be addressed in Phase F).
- Anything inside `app/ai_interview/` — this task is pure frontend plumbing against an already-stable backend contract.

**Acceptance criteria:**
1. An admin can view a list of all strategies and their latest version.
2. An admin can view full version history for a given strategy.
3. An admin can create a brand-new strategy (all `StrategyDefinition` fields, including nested `difficulty_policy`/`followup_policy`/`gap_policy`/`completion_policy`/`company_override_bounds`).
4. An admin can create a new version of an existing strategy.
5. An admin can activate/deactivate a specific version.
6. All five actions above call the real backend endpoints (no mock data) and are covered by at least a smoke-level frontend test.
7. No existing admin page, route, or backend endpoint is modified or broken by this change.
