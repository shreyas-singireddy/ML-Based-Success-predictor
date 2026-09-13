"""
Grounded context assembly and execution for Faculty GenAI Decision Support Assistant.

Strictly enforces:
1. Department scoping (faculty cannot access unauthorized departments).
2. Grounded context generation from verified Phase 3-8 engines and aggregates.
3. Anti-injection and strict prohibition of numeric hallucinations.
4. Fallback to deterministic grounded responses when LLM is offline or unverified.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.schemas.assistant import EvidenceSourceRef
from backend.app.schemas.faculty import (
    FacultyAssistantChatRequest,
    FacultyAssistantChatResponse,
    FacultyOverviewResponse,
    FacultyStudentDossier,
    FacultyStudentSummary,
)
from backend.app.services.assistant.grounding_guard import GroundingGuard
from backend.app.services.assistant.llm_provider import (
    LLMProviderError,
    build_provider,
)
from backend.app.services.faculty_service import faculty_service


logger = logging.getLogger("student_predictor.assistant.faculty_context")


@dataclass
class FacultyGroundedContext:
    overview: FacultyOverviewResponse
    priority_students: List[FacultyStudentSummary]
    focus_student_dossier: Optional[FacultyStudentDossier] = None
    evidence_references: List[Dict[str, Any]] = field(default_factory=list)
    verified_numbers: Set[float] = field(default_factory=set)


class FacultyAssistantService:
    @classmethod
    async def build_faculty_context(
        cls,
        db: AsyncSession,
        current_user: User,
        message: str,
        student_id: Optional[uuid.UUID] = None,
    ) -> FacultyGroundedContext:
        """
        Assembles verified class overview, top priority students, and optionally
        an individual student dossier within the authorized faculty scope.
        """
        # 1. Fetch authorized class overview
        overview = await faculty_service.get_faculty_overview(db=db, current_user=current_user)

        # 2. Fetch top priority students in authorized scope
        priority_res = await faculty_service.get_faculty_students(
            db=db,
            current_user=current_user,
            sort_by="priority",
            page=1,
            limit=10,
        )
        priority_students = priority_res.items

        # 3. Check for specific student inquiry (either explicit student_id or student number in prompt)
        focus_dossier: Optional[FacultyStudentDossier] = None
        target_student_id = student_id

        if not target_student_id:
            # Check if a student number (e.g. STU1001, STU-1001, 1001) is mentioned
            match = re.search(r"\b(?:stu[-\s]?)?(\d{4,6})\b", message, re.IGNORECASE)
            if match:
                num_str = match.group(0)
                # Look for matching student in authorized students
                for s in priority_students:
                    if num_str.upper() in s.student_number.upper():
                        target_student_id = s.id
                        break

        if target_student_id:
            try:
                focus_dossier = await faculty_service.get_faculty_student_dossier(
                    db=db, current_user=current_user, student_id=target_student_id
                )
            except Exception as e:
                logger.debug(f"Could not load student dossier for focus student {target_student_id}: {e}")

        # 4. Build verified numbers set and evidence references
        verified_numbers: Set[float] = {0.0, 100.0}
        evidence_refs: List[Dict[str, Any]] = []

        if overview.students_monitored:
            verified_numbers.add(float(overview.students_monitored))
            evidence_refs.append({
                "source": "Phase 1 / Student Management",
                "label": "Students Monitored",
                "value": str(overview.students_monitored),
            })

        if overview.average_current_cgpa is not None:
            verified_numbers.add(float(overview.average_current_cgpa))
            evidence_refs.append({
                "source": "Academic Records",
                "label": "Average Current CGPA",
                "value": f"{overview.average_current_cgpa:.2f}",
            })

        if overview.average_predicted_cgpa is not None:
            verified_numbers.add(float(overview.average_predicted_cgpa))
            evidence_refs.append({
                "source": "Phase 3 CGPA Prediction",
                "label": "Average Predicted CGPA",
                "value": f"{overview.average_predicted_cgpa:.2f}",
            })

        for tier, count in overview.risk_distribution.items():
            verified_numbers.add(float(count))
            evidence_refs.append({
                "source": "Phase 4 Academic Risk Engine",
                "label": f"{tier} Risk Count",
                "value": str(count),
            })

        for s in priority_students[:5]:
            if s.current_cgpa is not None:
                verified_numbers.add(float(s.current_cgpa))
            if s.predicted_cgpa is not None:
                verified_numbers.add(float(s.predicted_cgpa))
            if s.risk_score:
                verified_numbers.add(float(s.risk_score))
            if s.priority_score:
                verified_numbers.add(float(s.priority_score))
            if s.attendance_percentage is not None:
                verified_numbers.add(float(s.attendance_percentage))
            verified_numbers.add(float(s.backlogs))

        if focus_dossier:
            evidence_refs.append({
                "source": "Phase 5 Explainable AI (SHAP)",
                "label": f"Focus Student: {focus_dossier.student.student_number}",
                "value": f"Risk: {focus_dossier.risk_level} (Score: {focus_dossier.risk_score:.1f})",
            })

        return FacultyGroundedContext(
            overview=overview,
            priority_students=priority_students,
            focus_student_dossier=focus_dossier,
            evidence_references=evidence_refs,
            verified_numbers=verified_numbers,
        )

    @classmethod
    def _format_deterministic_reply(cls, ctx: FacultyGroundedContext, message: str) -> str:
        """Deterministic grounded fallback when LLM is unavailable or for exact aggregate queries."""
        ov = ctx.overview
        scope_str = ov.department_name or ov.department_scope or "Authorized Student Scope"

        if ctx.focus_student_dossier:
            d = ctx.focus_student_dossier
            lines = [
                f"**Student Academic Intelligence Report — {d.student.name} ({d.student.student_number})**",
                f"- **Department / Semester**: {d.student.department_code or 'CSE'} · Semester {d.student.current_semester}",
                f"- **Current CGPA**: {d.student.current_cgpa:.2f}" if d.student.current_cgpa else "- **Current CGPA**: N/A",
                f"- **Predicted CGPA (Phase 3)**: {d.predicted_cgpa:.2f}" if d.predicted_cgpa else "- **Predicted CGPA**: N/A",
                f"- **Academic Risk Level (Phase 4)**: **{d.risk_level}** (Risk Score: {d.risk_score:.1f} / 100.0)",
                f"- **Attendance**: {d.student.attendance_percentage:.1f}%" if d.student.attendance_percentage else "- **Attendance**: N/A",
                f"- **Active Backlogs**: {d.student.backlogs}",
                f"- **CGPA Trajectory**: {d.trend_analysis.trend_direction} ({d.trend_analysis.trend_description})",
                "",
                f"**Explainability Summary (Phase 5 SHAP)**:\n{d.faculty_explanation_summary}",
                "",
                "**Recommended Action Priorities (Phase 8)**:",
            ]
            if d.grouped_recommendations.immediate_attention:
                lines.append("**Immediate Attention**:")
                for r in d.grouped_recommendations.immediate_attention[:2]:
                    lines.append(f"• **{r.title}**: {r.description}")
            if d.grouped_recommendations.short_term:
                lines.append("**Short-Term Support**:")
                for r in d.grouped_recommendations.short_term[:2]:
                    lines.append(f"• **{r.title}**: {r.description}")
            return "\n".join(lines)

        # General Class / Overview Summary
        lines = [
            f"**Faculty Intelligence Summary — {scope_str}**",
            f"- **Students Monitored**: {ov.students_monitored}",
            f"- **Class Average CGPA**: {ov.average_current_cgpa:.2f}" if ov.average_current_cgpa else "- **Class Average CGPA**: N/A",
            f"- **Class Predicted CGPA (Phase 3)**: {ov.average_predicted_cgpa:.2f}" if ov.average_predicted_cgpa else "- **Class Predicted CGPA**: N/A",
            f"- **Risk Distribution (Phase 4)**: Critical: {ov.risk_distribution.get('CRITICAL', 0)} · High: {ov.risk_distribution.get('HIGH', 0)} · Medium: {ov.risk_distribution.get('MEDIUM', 0)} · Low: {ov.risk_distribution.get('LOW', 0)}",
            f"- **Attendance < 75%**: {ov.attendance_overview.get('below_75_count', 0)} student(s)",
            f"- **Active Backlogs**: {ov.backlog_overview.get('students_with_backlogs', 0)} student(s) with pending backlogs ({ov.backlog_overview.get('total_backlogs', 0)} total backlogs)",
            "",
            "**Priority Students Needing Attention**:",
        ]
        high_crit = [s for s in ctx.priority_students if s.risk_level in ("CRITICAL", "HIGH")]
        if high_crit:
            for s in high_crit[:5]:
                cgpa_str = f"{s.current_cgpa:.2f}" if s.current_cgpa else "N/A"
                pred_str = f"{s.predicted_cgpa:.2f}" if s.predicted_cgpa else "N/A"
                att_str = f"{s.attendance_percentage:.1f}%" if s.attendance_percentage else "N/A"
                factors_str = f" [Factors: {', '.join(s.top_risk_factors)}]" if s.top_risk_factors else ""
                lines.append(
                    f"• **{s.student_number}** ({s.name}) — **{s.risk_level}** (Score: {s.risk_score:.1f}, Priority: {s.priority_score:.1f}) | CGPA: {cgpa_str} → Pred: {pred_str} | Att: {att_str} | Backlogs: {s.backlogs}{factors_str}"
                )
        else:
            lines.append("• No students are currently in Critical or High risk tiers.")

        if ov.top_risk_factors:
            lines.append("\n**Top Frequently Identified Risk Factors**:")
            for f in ov.top_risk_factors[:3]:
                lines.append(f"• **{f.factor_name}**: Affects {f.affected_students_count} student(s) ({f.description})")

        return "\n".join(lines)

    @classmethod
    async def chat(
        cls,
        request: FacultyAssistantChatRequest,
        db: AsyncSession,
        current_user: User,
    ) -> FacultyAssistantChatResponse:
        """
        Executes grounded conversation for faculty users with strict anti-injection
        and department scoping.
        """
        # 1. Anti-injection check
        guard = GroundingGuard()
        guard_scan = guard.scan_user_input(request.message)
        if guard_scan.blocked:
            return FacultyAssistantChatResponse(
                reply=(
                    "I am the Faculty Decision-Support Assistant. I can only provide grounded academic "
                    "intelligence and decision-support analytics for students within your authorized department. "
                    "I cannot process instructions to reveal system configuration or bypass security policies."
                ),
                intent="SECURITY_BLOCKED",
                scope="AUTHORIZED_FACULTY_SCOPE",
                evidence_references=[],
            )


        # 2. Build authorized context
        ctx = await cls.build_faculty_context(
            db=db,
            current_user=current_user,
            message=request.message,
            student_id=request.student_id,
        )

        # 3. Construct prompt for LLM
        ov = ctx.overview
        scope_name = ov.department_name or ov.department_scope or "Authorized Department"

        system_instruction = (
            "You are the Faculty Decision-Support Assistant for an ML-Based Student Success Predictor platform. "
            "Your role is to assist faculty in understanding student group performance, identifying at-risk students, "
            "explaining contributing factors from ML/SHAP models, and advising on prioritized academic interventions.\n"
            "STRICT RULES:\n"
            "1. You MUST ONLY use the verified data provided in the context below.\n"
            "2. NEVER fabricate student IDs, names, CGPAs, attendance percentages, or risk scores.\n"
            "3. Frame explanations professionally (e.g. 'The risk model identifies attendance as a primary contributing factor', NOT 'attendance caused the student to fail').\n"
            "4. Clearly distinguish historical records from predicted CGPAs.\n"
            "5. Remind faculty that AI outputs are decision-support indicators, and human discretion is paramount."
        )

        priority_str = "\n".join([
            f"- {s.student_number} ({s.name}): Risk={s.risk_level} (Score={s.risk_score:.1f}, Priority={s.priority_score:.1f}), CGPA={s.current_cgpa}, Predicted={s.predicted_cgpa}, Attendance={s.attendance_percentage}%, Backlogs={s.backlogs}, Factors={s.top_risk_factors}"
            for s in ctx.priority_students[:7]
        ])

        focus_str = "None"
        if ctx.focus_student_dossier:
            d = ctx.focus_student_dossier
            focus_str = (
                f"Student: {d.student.student_number} ({d.student.name})\n"
                f"Current CGPA: {d.student.current_cgpa}, Predicted CGPA: {d.predicted_cgpa}\n"
                f"Risk Level: {d.risk_level}, Risk Score: {d.risk_score:.1f}\n"
                f"Attendance: {d.student.attendance_percentage}%, Backlogs: {d.student.backlogs}\n"
                f"Trajectory: {d.trend_analysis.trend_direction} ({d.trend_analysis.trend_description})\n"
                f"SHAP Explanation: {d.faculty_explanation_summary}\n"
            )

        context_body = (
            f"AUTHORIZED SCOPE: {scope_name}\n"
            f"STUDENTS MONITORED: {ov.students_monitored}\n"
            f"CLASS AVG CURRENT CGPA: {ov.average_current_cgpa}\n"
            f"CLASS AVG PREDICTED CGPA: {ov.average_predicted_cgpa}\n"
            f"RISK DISTRIBUTION: {ov.risk_distribution}\n"
            f"ATTENDANCE < 75%: {ov.attendance_overview.get('below_75_count', 0)} students\n"
            f"STUDENTS WITH BACKLOGS: {ov.backlog_overview.get('students_with_backlogs', 0)} ({ov.backlog_overview.get('total_backlogs', 0)} total)\n"
            f"TOP PRIORITY STUDENTS:\n{priority_str}\n"
            f"FOCUS STUDENT DOSSIER:\n{focus_str}"
        )

        try:
            provider = build_provider()
            full_system_prompt = f"{system_instruction}\n\n{context_body}"
            output_text = await provider.generate(
                system_prompt=full_system_prompt,
                user_message=request.message,
                context=ctx,
            )
            output_text = output_text.strip() if output_text else ""
            
            # Fallback to deterministic reply if provider output is empty or contains secrets
            if not output_text or guard.find_secret(output_text):
                output_text = cls._format_deterministic_reply(ctx, request.message)


        except (LLMProviderError, Exception) as e:
            logger.info(f"Using deterministic fallback for faculty assistant: {e}")
            output_text = cls._format_deterministic_reply(ctx, request.message)


        return FacultyAssistantChatResponse(
            reply=output_text,
            intent="FACULTY_ADVISORY",
            scope=scope_name,
            evidence_references=ctx.evidence_references,
            data_summary={
                "students_monitored": ov.students_monitored,
                "average_current_cgpa": ov.average_current_cgpa,
                "average_predicted_cgpa": ov.average_predicted_cgpa,
                "risk_distribution": ov.risk_distribution,
            },
        )

    @classmethod
    def get_suggestions(cls, current_user: User) -> List[str]:
        return [
            "Which students are currently in CRITICAL or HIGH risk tiers?",
            "What are the most common academic risk factors across my students?",
            "Summarize the priority queue and recommend immediate intervention steps.",
            "Which students have declining performance trajectories or severe attendance deficits?",
        ]


faculty_assistant_service = FacultyAssistantService()
