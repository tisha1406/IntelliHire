import re
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.schemas.strategy import StrategyDefinition, MixedComposition
from app.ai_interview.core.enums import (
    InterviewState, TopicState, RequirementCriticality,
    TopicDimension, TopicSource, ResumeEvidence, InterviewType
)
from app.ai_interview.blueprint_planning.enums import TopicSourceCode
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.runtime.exceptions import SessionInitializationError

# ---------------------------------------------------------------------------
# Source -> Dimension bridge (prerequisite fix for D-03).
#
# TopicBlueprint.source is a comma-joined, uppercase string of
# blueprint_planning.enums.TopicSourceCode names (e.g.
# "PROJECT_EVIDENCE,RESUME_SKILL"), produced by
# CoveragePlanner.plan() -- see blueprint_planning/coverage_planner.py:51:
#   source_str = ",".join(sorted([s.value for s in t.sources]))
#
# This is a DIFFERENT vocabulary from core.enums.TopicSource (resume |
# requirement | gap | behavioral), which TopicProgress.source now also
# resolves from this same TopicSourceCode string -- see the separate
# _resolve_topic_source_from_source_codes bridge further below (D-03
# prerequisite #2).
#
# Mapping rationale, per the architecture document's own evidence-source
# definitions (Section 2 of IntelliHire_Interview_Strategy_Architecture):
#   - Technical: "campaign required/preferred skills + resume tech stack"
#     -> ROLE_REQUIRED (campaign-required skill) and RESUME_SKILL (a resume
#        tech-stack entry) both represent technical evidence.
#   - Resume / Experience: "resume projects/roles only"
#     -> PROJECT_EVIDENCE and EXPERIENCE_EVIDENCE both come from a resume
#        project or role entry, not a bare skill name.
#   - MODE_REQUIRED: today TopicSelector.select_topics() only ever produces
#     ONE mode-required topic, hardcoded as "Behavioral & Situational"
#     (blueprint_planning/topic_selector.py:49) when the interview mode's
#     allowed_question_types includes "behavioral". It is therefore mapped
#     to BEHAVIORAL here.
#   - SITUATIONAL_SCENARIO (D-03): a topic sourced from the deterministic
#     scenario bank (ScenarioRepository), added by TopicSelector only when
#     the campaign's interview_type/mixed_composition requests situational
#     coverage. Maps directly to TopicDimension.SITUATIONAL -- the one
#     dimension no other source code can produce. This is what makes
#     ShadowPriorityCalculator's existing SITUATIONAL composition-score
#     branch (runtime/shadow_priority_calculator.py:84-85) reachable for the
#     first time; that branch required no changes of its own.
_SOURCE_CODE_TO_DIMENSION: Dict[TopicSourceCode, TopicDimension] = {
    TopicSourceCode.MODE_REQUIRED: TopicDimension.BEHAVIORAL,
    TopicSourceCode.ROLE_REQUIRED: TopicDimension.TECHNICAL,
    TopicSourceCode.PROJECT_EVIDENCE: TopicDimension.RESUME,
    TopicSourceCode.EXPERIENCE_EVIDENCE: TopicDimension.RESUME,
    TopicSourceCode.RESUME_SKILL: TopicDimension.TECHNICAL,
    TopicSourceCode.SITUATIONAL_SCENARIO: TopicDimension.SITUATIONAL,
}

# Precedence order used when a single topic carries multiple source codes
# (TopicSelector can tag one topic with several sources -- e.g. a skill that
# is both a campaign requirement and found in a resume project). This
# mirrors PriorityAllocator's own already-established precedence exactly
# (blueprint_planning/priority_allocator.py: RESUME_SKILL=2 <
# PROJECT_EVIDENCE/EXPERIENCE_EVIDENCE=3 < ROLE_REQUIRED=4 <
# MODE_REQUIRED=SITUATIONAL_SCENARIO=5), so the same source that would win
# priority allocation also determines the topic's dimension -- consistent
# with the architecture document's "requirements guarantee, resume
# personalizes" principle (Section 10): a campaign requirement outranks
# resume-only evidence. SITUATIONAL_SCENARIO is placed first (D-03): like
# MODE_REQUIRED it represents a deliberate campaign-level configuration
# decision rather than opportunistic candidate/requirement evidence, and
# PriorityAllocator gives it the same top priority (5) -- in the extremely
# unlikely event a scenario's topic_name collides with another selected
# topic's name, the explicit situational pick should not be silently
# demoted. _resolve_topic_source_from_source_codes (further below) does not
# special-case this code, so when it is the only code present the loop
# simply falls through to its final `return None` -- correct, since
# core.enums.TopicSource has no situational value and nothing consumes one.
_SOURCE_CODE_PRECEDENCE: List[TopicSourceCode] = [
    TopicSourceCode.SITUATIONAL_SCENARIO,
    TopicSourceCode.MODE_REQUIRED,
    TopicSourceCode.ROLE_REQUIRED,
    TopicSourceCode.PROJECT_EVIDENCE,
    TopicSourceCode.EXPERIENCE_EVIDENCE,
    TopicSourceCode.RESUME_SKILL,
]


def _resolve_dimension_from_source_codes(source_str: Optional[str]) -> Optional[TopicDimension]:
    """
    Parses TopicBlueprint.source (the real, comma-joined TopicSourceCode
    string produced by CoveragePlanner) into a single TopicDimension, using
    the precedence order above when multiple codes are present.

    Returns None only if the string is empty/unparseable (defensive; should
    not occur for topics produced by the real TopicSelector/CoveragePlanner
    pipeline, and also correctly handles hand-constructed test fixtures that
    don't set .source at all).
    """
    if not source_str:
        return None
    codes = set()
    for part in source_str.split(","):
        part = part.strip().upper()
        try:
            codes.add(TopicSourceCode(part))
        except ValueError:
            continue
    for code in _SOURCE_CODE_PRECEDENCE:
        if code in codes:
            return _SOURCE_CODE_TO_DIMENSION[code]
    return None


# ---------------------------------------------------------------------------
# Source-code -> TopicProgress.source bridge (D-03 prerequisite #2).
#
# TopicProgress.source uses core.enums.TopicSource (resume | requirement |
# gap | behavioral) -- the vocabulary question_turn_planner.py's gap
# verification routing (line ~130: `if topic_progress.source ==
# TopicSource.GAP`) and prompt_library.py's S_GAP_VERIFICATION strategy
# actually consume. It is NOT the same vocabulary as TopicSourceCode, so the
# mapping below is a deliberate semantic resolution, not a mechanical
# enum-name translation.
#
# RESUME is the direct match for the three resume-derived codes: RESUME_SKILL
# (a resume skill entry), PROJECT_EVIDENCE and EXPERIENCE_EVIDENCE (a resume
# project/role entry) -- TopicSource has no separate "project"/"experience"
# value, so all three collapse to RESUME, consistent with specs.md's
# Resume/Experience dimension description ("resume projects/roles only").
#
# BEHAVIORAL is the direct match for MODE_REQUIRED, for the same reason as
# the dimension bridge above: today TopicSelector only ever produces one
# mode-required topic ("Behavioral & Situational").
#
# ROLE_REQUIRED is the one genuinely ambiguous code, and is NOT a 1:1 match
# to either REQUIREMENT or GAP alone -- it resolves to one or the other
# depending on resume_evidence, which SessionInitializer already computes
# independently (see resume_evidence above, a few lines up in initialize()):
#   - GAP never exists as its own TopicSourceCode. Per specs.md:166 ("Gap
#     verification (resume-absent requirements)") and question_turn_planner's
#     own S_GAP_VERIFICATION prompt text ("verifying a specific campaign
#     requirement that lacks clear resume evidence"), a "gap" topic is
#     precisely a campaign requirement (ROLE_REQUIRED) that is ABSENT from
#     the resume. That is exactly what ROLE_REQUIRED + ResumeEvidence.ABSENT
#     represents -- so GAP is a DERIVED combination of an existing source
#     code and the already-computed resume_evidence, not a new value we are
#     inventing.
#   - When the same ROLE_REQUIRED topic IS present on the resume
#     (resume_evidence is PARTIAL/STRONG), it is a confirmed requirement, not
#     a gap -- TopicSource.REQUIREMENT, which matches the architecture
#     document's "Present + Campaign Requires=Yes" confirming-question case.
#
# Multi-source-code topics reuse the SAME precedence order as the dimension
# bridge above (_SOURCE_CODE_PRECEDENCE, itself mirroring
# PriorityAllocator's own established precedence) rather than a second,
# unrelated priority scheme -- the source code that wins dimension/priority
# resolution also determines TopicProgress.source.
def _resolve_topic_source_from_source_codes(
    source_str: Optional[str], resume_evidence: ResumeEvidence
) -> Optional[TopicSource]:
    """
    Parses TopicBlueprint.source (the real TopicSourceCode string) into
    core.enums.TopicSource, using resume_evidence to disambiguate
    ROLE_REQUIRED between REQUIREMENT and GAP (see module-level comment
    above for the full justification).

    Returns None only if the string is empty/unparseable (defensive; mirrors
    _resolve_dimension_from_source_codes).
    """
    if not source_str:
        return None
    codes = set()
    for part in source_str.split(","):
        part = part.strip().upper()
        try:
            codes.add(TopicSourceCode(part))
        except ValueError:
            continue
    for code in _SOURCE_CODE_PRECEDENCE:
        if code not in codes:
            continue
        if code == TopicSourceCode.MODE_REQUIRED:
            return TopicSource.BEHAVIORAL
        if code == TopicSourceCode.ROLE_REQUIRED:
            if resume_evidence == ResumeEvidence.ABSENT:
                return TopicSource.GAP
            return TopicSource.REQUIREMENT
        if code in (
            TopicSourceCode.PROJECT_EVIDENCE,
            TopicSourceCode.EXPERIENCE_EVIDENCE,
            TopicSourceCode.RESUME_SKILL,
        ):
            return TopicSource.RESUME
    return None


# ---------------------------------------------------------------------------
# Resume evidence (ABSENT / PARTIAL / STRONG).
#
#   STRONG  - the topic name equals a skill the resume lists (unchanged).
#   PARTIAL - the topic is a campaign-required item that is NOT a listed
#             skill, but the resume's own text mentions it as a whole word:
#             another skill entry (e.g. "Kubernetes Administration"), an
#             experience title/description, a project name/description or a
#             certification name. It is related/incomplete evidence: the
#             resume talks about it without listing it as a skill.
#   ABSENT  - neither.
#
# Deliberately deterministic and literal (case-insensitive whole-word match;
# no stemming, synonyms, fuzzy or semantic matching). Limits, by design:
#   - only ROLE_REQUIRED topics can become PARTIAL (the "requested item" the
#     evidence state is about); other topics keep their previous evidence, so
#     PARTIAL cannot silently reorder resume-derived topics;
#   - names shorter than _MIN_TEXT_MATCH_LEN (e.g. "Go", "R", "C") are only
#     ever STRONG via the skills list, because as prose words they are
#     indistinguishable from ordinary text;
#   - education and interview-time claims are never consulted.
# Downstream PARTIAL handling already existed and is unchanged: priority
# weight 0.5 (ShadowPriorityCalculator), source REQUIREMENT not GAP
# (_resolve_topic_source_from_source_codes), value passed through to prompts
# and reports.
# ---------------------------------------------------------------------------
_MIN_TEXT_MATCH_LEN = 3


def _resume_text_fragments(structured_resume, exclude_skill_name: str) -> List[str]:
    fragments: List[str] = []
    for skill in structured_resume.skills:
        name = skill.name.lower().strip()
        if name and name != exclude_skill_name:
            fragments.append(name)
    for exp in structured_resume.experience:
        fragments.append(exp.title or "")
        fragments.append(exp.description or "")
    for project in structured_resume.projects:
        fragments.append(project.name or "")
        fragments.append(project.description or "")
    for cert in structured_resume.certifications:
        fragments.append(cert.name or "")
    return [f.lower() for f in fragments if f]


def _mentions_as_whole_word(name_lower: str, text_lower: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(name_lower) + r"(?![a-z0-9])"
    return re.search(pattern, text_lower) is not None


def _resolve_resume_evidence(topic, structured_resume) -> ResumeEvidence:
    if structured_resume is None:
        return ResumeEvidence.ABSENT
    name = topic.topic_name.lower().strip()
    if name in [s.name.lower().strip() for s in structured_resume.skills]:
        return ResumeEvidence.STRONG
    is_required = "ROLE_REQUIRED" in [p.strip().upper() for p in (topic.source or "").split(",")]
    if is_required and len(name) >= _MIN_TEXT_MATCH_LEN:
        if any(_mentions_as_whole_word(name, f) for f in _resume_text_fragments(structured_resume, name)):
            return ResumeEvidence.PARTIAL
    return ResumeEvidence.ABSENT


class SessionInitializer:
    @staticmethod
    def initialize(
        blueprint: InterviewBlueprint,
        candidate_id: str,
        company_id: str,
        campaign_id: str,
        mode_id: str,
        mode_version: int,
        session_id: str = None,
        strategy_snapshot: Optional[StrategyDefinition] = None,
        interview_type: Optional[InterviewType] = None,
        mixed_composition: Optional[MixedComposition] = None,
        campaign_requirements: Optional[list] = None,
        candidate_context: Optional[CandidateInterviewContext] = None,
        voice_id: Optional[str] = None
    ) -> InterviewSessionSchema:
        """
        Creates a runtime InterviewSession schema securely binding an immutable blueprint.
        Ensures exact TopicProgress creation. Counters start at zero.
        """
        if not blueprint.topics:
            raise SessionInitializationError("Cannot initialize session with empty blueprint.")

        # Build requirement mapping
        req_map: Dict[str, RequirementCriticality] = {}
        req_str_map: Dict[str, str] = {}
        if campaign_requirements:
            for req in campaign_requirements:
                if isinstance(req, dict):
                    original_skill = str(req.get("skill", "")).strip()
                    skill = original_skill.lower()
                    crit = req.get("criticality")
                    if skill and crit:
                        try:
                            req_map[skill] = RequirementCriticality(str(crit).lower())
                            req_str_map[skill] = original_skill
                        except ValueError:
                            pass

        # Prevent duplicate topic progress entries
        unique_topic_ids = set()
        progress_list = []
        for topic in blueprint.topics:
            if topic.topic_id in unique_topic_ids:
                raise SessionInitializationError(f"Duplicate blueprint topic ID found: {topic.topic_id}")
            unique_topic_ids.add(topic.topic_id)
            
            topic_name_lower = topic.topic_name.lower().strip()
            
            # Determine Criticality
            criticality = req_map.get(topic_name_lower)
            
            # Determine original campaign requirement string
            campaign_req_str = req_str_map.get(topic_name_lower)
            
            # Determine Resume Evidence
            resume_evidence = _resolve_resume_evidence(
                topic,
                candidate_context.structured_resume if candidate_context else None,
            )
                
            # Determine Source (core.enums.TopicSource vocabulary -- resume |
            # requirement | gap | behavioral) from the REAL TopicSourceCode
            # vocabulary that TopicSelector/CoveragePlanner actually produce,
            # using resume_evidence (computed just above) to disambiguate
            # ROLE_REQUIRED between REQUIREMENT and GAP. See the module-level
            # _resolve_topic_source_from_source_codes comment for the full
            # mapping justification.
            source = _resolve_topic_source_from_source_codes(topic.source, resume_evidence)

            # Determine Dimension from the REAL TopicSourceCode vocabulary
            # that TopicSelector/CoveragePlanner actually produce (see the
            # module-level _resolve_dimension_from_source_codes above).
            dimension = _resolve_dimension_from_source_codes(topic.source)

            progress_list.append(
                TopicProgress(
                    topic_id=topic.topic_id,
                    state=TopicState.NOT_STARTED,
                    criticality=criticality,
                    dimension=dimension,
                    source=source,
                    resume_evidence=resume_evidence,
                    campaign_requirement=campaign_req_str,
                    structurally_attempted=False,
                    qualitatively_covered=False,
                    coverage_score=0.0,
                    readiness_score=0.0,
                    follow_up_count=0
                )
            )

        return InterviewSessionSchema(
            session_id=session_id or str(uuid.uuid4()),
            candidate_id=candidate_id,
            company_id=company_id,
            campaign_id=campaign_id,
            mode_id=mode_id,
            mode_version=mode_version,
            strategy_snapshot=strategy_snapshot,
            interview_type=interview_type,
            mixed_composition=mixed_composition,
            state=InterviewState.CREATED,
            blueprint=blueprint,
            questions_asked_total=0,
            voice_id=voice_id,
            current_topic_id=None,
            current_difficulty=None,
            topic_progress=progress_list,
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            failure_reason=None
        )
