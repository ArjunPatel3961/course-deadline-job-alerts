from datetime import datetime, timezone

from course_job_monitor.course_delivery import JobStatus, ScheduledCourseJob, evaluate_course_delivery


class RecordingErrors:
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, object], str]] = []

    def capture(self, exception_payload: dict[str, object], idempotency_key: str) -> dict[str, object]:
        self.calls.append((exception_payload, idempotency_key))
        return {"event_id": "event-edtech-1"}


def test_overdue_undelivered_course_alerts_the_educator() -> None:
    errors = RecordingErrors()
    job = ScheduledCourseJob(
        job_id="delivery-17",
        course_id="biology-201",
        learner_id="learner-42",
        educator_id="educator-7",
        scheduled_for="2026-08-21T08:00:00Z",
        learner_deadline="2026-08-21T09:00:00Z",
    )

    report = evaluate_course_delivery(
        job,
        errors,
        now=datetime(2026, 8, 21, 9, 5, tzinfo=timezone.utc),
    )

    assert report.status is JobStatus.ALERTED
    assert report.alert_event_id == "event-edtech-1"
    payload, key = errors.calls[0]
    assert payload["fingerprint"] == ["course-delivery", "biology-201", "delivery-17"]
    assert key.startswith("course-delivery:delivery-17:")


def test_delivered_course_does_not_create_an_alert() -> None:
    errors = RecordingErrors()
    job = ScheduledCourseJob(
        job_id="delivery-18",
        course_id="history-101",
        learner_id="learner-9",
        educator_id="educator-3",
        scheduled_for="2026-08-21T08:00:00Z",
        learner_deadline="2026-08-21T09:00:00Z",
        delivered_at="2026-08-21T08:45:00Z",
    )

    report = evaluate_course_delivery(
        job,
        errors,
        now=datetime(2026, 8, 21, 9, 5, tzinfo=timezone.utc),
    )

    assert report.status is JobStatus.COMPLETED
    assert errors.calls == []
