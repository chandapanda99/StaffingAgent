from __future__ import annotations

import re

from app.core.config import Settings
from app.domain.enums import MessageCategory
from app.domain.schemas import (
    JobDescriptionExtraction,
    MatchCandidate,
    MatchFactor,
    ResumeExtraction,
)


class OpenAIPlaceholderAdapter:
    provider_name = "heuristic-local"
    _SKILL_PATTERN = re.compile(r"\b(Python|FastAPI|SQLAlchemy|PostgreSQL|AWS|Docker|Terraform|React|Java|Node\.js)\b", re.I)

    def __init__(self, model: str) -> None:
        self.model = model

    @classmethod
    def from_settings(cls, settings: Settings) -> "OpenAIPlaceholderAdapter":
        return cls(model=settings.openai_model)

    def classify(self, subject: str, body_text: str, sender: str) -> tuple[MessageCategory, float, str]:
        haystack = f"{subject}\n{body_text}\n{sender}".lower()
        if any(token in haystack for token in ["job", "role", "position", "required skills", "preferred skills", "full-time"]):
            return (
                MessageCategory.job_posting,
                0.82,
                "Heuristic classification matched hiring-oriented language in the message content.",
            )
        if any(token in haystack for token in ["resume", "cv", "skills:", "experience:", "contractor", "candidate"]):
            return (
                MessageCategory.contractor,
                0.87,
                "Heuristic classification matched resume or candidate-oriented language in the message body.",
            )
        return (
            MessageCategory.other,
            0.51,
            "Heuristic classification could not confidently identify the message as a contractor profile or job posting.",
        )

    def extract_resume(self, subject: str, body_text: str, sender: str) -> ResumeExtraction:
        skills = self._extract_skills(body_text)
        email = self._search(r"Email:\s*([^\s]+@[^\s]+)", body_text) or self._search(r"([^\s]+@[^\s]+)", body_text)
        phone = self._search(r"Phone:\s*([\d\-\+\(\)\s]+)", body_text)
        location = self._search(r"Location:\s*(.+)", body_text)
        experience = self._search_float(r"Experience:\s*([0-9]+(?:\.[0-9]+)?)", body_text)
        full_name = self._extract_name(subject, body_text, sender)
        summary = self._summarize_text(body_text)
        return ResumeExtraction(
            full_name=full_name,
            email=email,
            phone=phone.strip() if phone else None,
            location=location.strip() if location else None,
            skills=skills,
            experience_years=experience,
            summary=summary,
        )

    def extract_job(self, subject: str, body_text: str, sender: str) -> JobDescriptionExtraction:
        required_skills = self._extract_skills(body_text)
        preferred_skills = self._extract_preferred_skills(body_text)
        title = self._extract_job_title(subject)
        company = self._infer_company(sender)
        location = self._search(r"(?:Location|located in):\s*(.+)", body_text)
        employment_type = self._search(r"\b(full-time|contract|contract-to-hire|part-time)\b", body_text, flags=re.I)
        summary = self._summarize_text(body_text)
        return JobDescriptionExtraction(
            title=title,
            company=company,
            location=location.strip() if location else None,
            employment_type=employment_type.lower() if employment_type else None,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            summary=summary,
        )

    def match(
        self,
        *,
        job_posting_id: str,
        job_required_skills: list[str],
        job_preferred_skills: list[str],
        job_location: str | None,
        profiles: list[dict],
        limit: int,
    ) -> list[MatchCandidate]:
        candidates: list[MatchCandidate] = []
        for profile in profiles:
            factors = self._build_match_factors(
                profile_skills=profile["skills"],
                profile_location=profile["location"],
                profile_experience_years=profile["experience_years"],
                job_required_skills=job_required_skills,
                job_preferred_skills=job_preferred_skills,
                job_location=job_location,
            )
            score = round(sum(factor.score * factor.weight for factor in factors), 4)
            candidates.append(
                MatchCandidate(
                    contractor_profile_id=profile["id"],
                    score=score,
                    summary=self._build_match_summary(profile["full_name"], score, factors),
                    factors=factors,
                )
            )
        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        return candidates[:limit]

    def _extract_skills(self, text: str) -> list[str]:
        seen: dict[str, str] = {}
        for match in self._SKILL_PATTERN.findall(text):
            normalized = match.lower()
            seen.setdefault(normalized, match)
        return list(seen.values())

    def _extract_preferred_skills(self, text: str) -> list[str]:
        preferred_section = self._search(r"Preferred skills:\s*(.+)", text)
        if not preferred_section:
            return []
        return self._extract_skills(preferred_section)

    def _extract_name(self, subject: str, body_text: str, sender: str) -> str | None:
        subject_name = self._search(r"resume submission\s*-\s*([A-Za-z ,.'-]+)", subject, flags=re.I)
        if subject_name:
            return subject_name.strip()

        first_line = body_text.splitlines()[0].strip() if body_text.splitlines() else ""
        if first_line and len(first_line.split()) <= 4 and "@" not in first_line and ":" not in first_line:
            return first_line

        sender_name = sender.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
        return sender_name.title() if sender_name else None

    def _extract_job_title(self, subject: str) -> str | None:
        match = self._search(r"(.+?)(?:\s*-\s*.+)?$", subject)
        return match.strip() if match else None

    def _infer_company(self, sender: str) -> str | None:
        if "@" not in sender:
            return None
        domain = sender.split("@", 1)[1].split(".", 1)[0]
        return domain.replace("-", " ").title()

    def _summarize_text(self, text: str) -> str:
        compact = " ".join(part.strip() for part in text.splitlines() if part.strip())
        return compact[:280]

    def _build_match_factors(
        self,
        *,
        profile_skills: list[str],
        profile_location: str | None,
        profile_experience_years: float | None,
        job_required_skills: list[str],
        job_preferred_skills: list[str],
        job_location: str | None,
    ) -> list[MatchFactor]:
        profile_skill_set = {skill.lower() for skill in profile_skills}
        required_set = {skill.lower() for skill in job_required_skills}
        preferred_set = {skill.lower() for skill in job_preferred_skills}

        required_overlap = len(profile_skill_set & required_set)
        required_total = len(required_set) or 1
        required_score = required_overlap / required_total

        preferred_overlap = len(profile_skill_set & preferred_set)
        preferred_total = len(preferred_set) or 1
        preferred_score = preferred_overlap / preferred_total if preferred_set else 1.0

        location_score = 1.0
        if job_location and profile_location:
            location_score = 1.0 if job_location.lower() in profile_location.lower() else 0.4
        elif job_location and not profile_location:
            location_score = 0.3

        experience_score = min((profile_experience_years or 0.0) / 8.0, 1.0)

        return [
            MatchFactor(
                name="required_skills",
                score=round(required_score, 4),
                weight=0.5,
                explanation=f"Matched {required_overlap} of {len(required_set)} required skills.",
            ),
            MatchFactor(
                name="preferred_skills",
                score=round(preferred_score, 4),
                weight=0.2,
                explanation=f"Matched {preferred_overlap} preferred skills.",
            ),
            MatchFactor(
                name="location_alignment",
                score=round(location_score, 4),
                weight=0.1,
                explanation="Profile location aligns with the job location." if location_score >= 1.0 else "Location is missing or only partially aligned.",
            ),
            MatchFactor(
                name="experience_depth",
                score=round(experience_score, 4),
                weight=0.2,
                explanation="Experience was normalized against an eight-year target for ranking.",
            ),
        ]

    def _build_match_summary(self, full_name: str | None, score: float, factors: list[MatchFactor]) -> str:
        strongest = max(factors, key=lambda factor: factor.score * factor.weight)
        candidate_name = full_name or "Candidate"
        return f"{candidate_name} scored {score:.2f}; strongest factor was {strongest.name}."

    def _search(self, pattern: str, text: str, *, flags: int = 0) -> str | None:
        match = re.search(pattern, text, flags)
        if not match:
            return None
        return match.group(1)

    def _search_float(self, pattern: str, text: str) -> float | None:
        match = self._search(pattern, text)
        return float(match) if match else None
