from app.db.repositories.workflows import WorkflowRepository
from app.domain.schemas import MatchCandidate, MatchFactor, MatchResultResponse, MatchRunRequest, MatchRunResponse
from fastapi import HTTPException
from sqlalchemy.orm import Session


class MatchingService:
    def __init__(self, db: Session, matcher) -> None:
        self.db = db
        self.matcher = matcher

    def run(self, payload: MatchRunRequest) -> MatchRunResponse:
        repository = WorkflowRepository(self.db)
        job_posting = repository.get_job_posting(payload.job_posting_id)
        if job_posting is None:
            raise HTTPException(status_code=404, detail=f"Job posting {payload.job_posting_id} was not found.")

        profiles = repository.list_contractor_profiles()
        if not profiles:
            raise HTTPException(status_code=400, detail="No contractor profiles are available to score.")

        match_run = repository.create_match_run(
            job_posting_id=payload.job_posting_id,
            requested_by=payload.requested_by,
            status="running",
        )
        candidates = self.matcher.match(
            job_posting_id=job_posting.id,
            job_required_skills=job_posting.required_skills_json,
            job_preferred_skills=job_posting.preferred_skills_json,
            job_location=job_posting.location,
            profiles=[
                {
                    "id": profile.id,
                    "full_name": profile.full_name,
                    "skills": profile.skills_json,
                    "location": profile.location,
                    "experience_years": profile.experience_years,
                }
                for profile in profiles
            ],
            limit=payload.limit,
        )
        repository.replace_match_results(
            match_run_id=match_run.id,
            candidates=[
                {
                    "contractor_profile_id": candidate.contractor_profile_id,
                    "score": candidate.score,
                    "summary": candidate.summary,
                    "factor_breakdown_json": [factor.model_dump() for factor in candidate.factors],
                }
                for candidate in candidates
            ],
        )
        repository.update_match_run_status(match_run_id=match_run.id, status="completed")
        self.db.commit()
        return MatchRunResponse(
            match_run_id=match_run.id,
            status="completed",
            placeholder=False,
            detail=f"Generated {len(candidates)} ranked candidates for job posting {job_posting.id}.",
        )

    def get(self, match_run_id: str) -> MatchResultResponse:
        repository = WorkflowRepository(self.db)
        match_run = repository.get_match_run(match_run_id)
        if match_run is None:
            raise HTTPException(status_code=404, detail=f"Match run {match_run_id} was not found.")

        match_results = repository.list_match_results(match_run_id)
        return MatchResultResponse(
            match_run_id=match_run_id,
            status=match_run.status,
            candidates=[
                MatchCandidate(
                    contractor_profile_id=result.contractor_profile_id,
                    score=result.score,
                    summary=result.summary or "",
                    factors=[MatchFactor.model_validate(factor) for factor in result.factor_breakdown_json],
                )
                for result in match_results
            ],
            placeholder=False,
        )
