"""HTTP entry point for the scheduler and educator reporting workflow."""

from fastapi import Depends, FastAPI, HTTPException

from .course_delivery import JobReport, ScheduledCourseJob, evaluate_course_delivery
from .infrai_errors import InfraiError, InfraiErrors

service = FastAPI(title="Course Job Monitor")


def error_client() -> InfraiErrors:
    return InfraiErrors()


@service.post("/scheduled-jobs/run", response_model=JobReport)
def run_scheduled_job(
    job: ScheduledCourseJob,
    errors: InfraiErrors = Depends(error_client),
) -> JobReport:
    try:
        return evaluate_course_delivery(job, errors)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "error": exc.details},
        ) from exc
