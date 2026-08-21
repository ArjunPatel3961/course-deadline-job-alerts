"""Business decision for a scheduled course-delivery run."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    COMPLETED = "completed"
    ALERTED = "alerted"


class ScheduledCourseJob(BaseModel):
    job_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    learner_id: str = Field(min_length=1)
    educator_id: str = Field(min_length=1)
    scheduled_for: datetime
    learner_deadline: datetime
    delivered_at: datetime | None = None


class JobReport(BaseModel):
    job_id: str
    course_id: str
    learner_id: str
    educator_id: str
    status: JobStatus
    alert_event_id: str | None = None


def evaluate_course_delivery(
    job: ScheduledCourseJob,
    errors: Any,
    now: datetime | None = None,
) -> JobReport:
    """Alert when delivery is still missing after the learner deadline."""
    observed_at = now or datetime.now(timezone.utc)
    deadline = job.learner_deadline
    if deadline.tzinfo is None or observed_at.tzinfo is None:
        raise ValueError("learner_deadline and now must include a timezone")

    if job.delivered_at is not None or observed_at <= deadline:
        return JobReport(**job.model_dump(include={"job_id", "course_id", "learner_id", "educator_id"}), status=JobStatus.COMPLETED)

    data = errors.capture(
        exception_payload={
            "title": "Course delivery missed learner deadline",
            "message": f"Scheduled job {job.job_id} did not deliver course {job.course_id}",
            "level": "error",
            "fingerprint": ["course-delivery", job.course_id, job.job_id],
            "exception": {
                "type": "CourseDeliveryDeadlineMissed",
                "value": "Course content was not delivered before the learner deadline",
            },
            "context": {
                "job_id": job.job_id,
                "course_id": job.course_id,
                "learner_id": job.learner_id,
                "educator_id": job.educator_id,
                "scheduled_for": job.scheduled_for.isoformat(),
                "learner_deadline": deadline.isoformat(),
                "observed_at": observed_at.isoformat(),
            },
        },
        idempotency_key=f"course-delivery:{job.job_id}:{deadline.isoformat()}",
    )
    return JobReport(
        job_id=job.job_id,
        course_id=job.course_id,
        learner_id=job.learner_id,
        educator_id=job.educator_id,
        status=JobStatus.ALERTED,
        alert_event_id=str(data["event_id"]),
    )
