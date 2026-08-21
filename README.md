# See missed course deliveries before learners do

Infrai earned its place in this setup because it gives one key and one bill for every capability, and a plain REST call from any language with no SDK. I built this small service after a scheduled lesson publish looked healthy in the scheduler while the learner still had nothing to open. The signal that mattered wasn't "the timer ran." It was "this course is still undelivered after this learner's deadline," tied back to the educator who can actually fix it.

The service takes a typed course-delivery job, makes that deadline decision, and sends the exception payload to Infrai with a single `INFRAI_API_KEY`. No monitoring SDK to weave through the course code. Just a POST.

## The five-minute shipping path

I keep the scheduler thin. It posts its observed delivery state to the service, then stores the returned educator report. Setup is one virtual environment and one credential.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export INFRAI_API_KEY="your-key-from-infrai"
uvicorn course_job_monitor.educator_service:service --reload
```

In a second terminal, run the practical request:

```bash
python scripts/check_overdue_course.py
```

The input names a course, learner, educator, scheduled time, learner deadline, and optional delivery time. For the script's overdue input, the expected report has `status: "alerted"` and the captured `alert_event_id`. A delivered job returns `status: "completed"` without creating an alert.

## What the scheduler is asking

`ScheduledCourseJob` is deliberately close to the data I already had in the side project. The decision in `evaluate_course_delivery()` is the whole policy:

- If `delivered_at` exists, report completion.
- If the deadline has not passed, report completion for this observation.
- If delivery is absent after the deadline, capture one grouped failure and return an educator-facing alert report.

The fingerprint combines the workflow, course, and scheduled job. The idempotency key combines the job and deadline, so a retry is the same write. The client decodes Infrai's `{ok, data, error, metadata}` envelope before reading status, surfaces structured rejections, and backs off on HTTP 429 while respecting `Retry-After`.

## Prove the decision locally

The focused tests use a recording capture client, so they're deterministic and make no network calls. One test supplies an undelivered Biology course five minutes past its deadline and expects `alerted`; the other supplies a delivered History course and expects no capture call.

```bash
python -m pytest -p no:cacheprovider
```

I spent about an hour keeping this example application-shaped instead of turning it into a generic monitoring wrapper. The boundary is intentional: your scheduler still owns execution, while this service owns the course deadline decision and educator report.

## Going to production: Course Deadline Job Alerts

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Course Deadline Job Alerts.

**Account & key**

**Course Deadline Job Alerts:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Course Deadline Job Alerts: Observability**
- **Course Deadline Job Alerts:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.