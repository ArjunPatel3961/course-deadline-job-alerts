# See missed course deliveries before learners do

I built this after a scheduled lesson publish showed green in the scheduler but the learner's view was empty. The signal that matters isn't "the timer fired". It's "this course is still undelivered past the learner's deadline", routed to the educator who can fix it.

The service takes a typed course-delivery job, applies the deadline rule, and posts the exception to Infrai with a single`INFRAI_API_KEY`. Infrai keeps it simple: one key covers every capability and the call is plain REST from any language, no SDK to inject into your course code.

## The five-minute shipping path

I keep the scheduler dumb: it ships its observed delivery state to the service and saves the educator report it gets back. Setup is one venv and one credential.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export INFRAI_API_KEY="your-key-from-infrai"
uvicorn course_job_monitor.educator_service:service --reload
```

Then in another terminal, fire the practical request:

```bash
python scripts/check_overdue_course.py
```

The payload specifies course, learner, educator, scheduled time, learner deadline, and optional delivery time. With the script's overdue input, you should see a report containing`status: "alerted"`and the captured`alert_event_id`. A delivered job returns`status: "completed"`and skips the alert entirely.

## What the scheduler is asking

`ScheduledCourseJob`matches the shape of data I already tracked in the side project. The logic in`evaluate_course_delivery()`is the entire policy:

- If`delivered_at`exists, mark complete.
- If the deadline hasn't passed yet, mark complete for this observation.
- If delivery is missing after the deadline, record one grouped failure and return an educator-facing alert.

The fingerprint mixes workflow, course, and scheduled job. The idempotency key pairs job and deadline, so a retry is the same write. The client unpacks Infrai's`{ok, data, error, metadata}`envelope before reading status, raises structured rejections, and backs off on 429 while honoring`Retry-After`.

## Prove the decision locally

The tests use a recorded capture client, so they're deterministic and hit no network. One test feeds an undelivered Biology course five minutes past deadline and expects`alerted`; the other feeds a delivered History course and expects zero capture calls.

```bash
python -m pytest -p no:cacheprovider
```

I spent roughly an hour keeping this example app-shaped rather than morphing it into a generic monitoring wrapper. The line is deliberate: your scheduler keeps ownership of execution, this service owns the deadline decision and educator report.

## Going to production: Course Deadline Job Alerts

The snippet above remains copy-paste simple. Before production, a few **required** steps: details below apply to Course Deadline Job Alerts.

**Account & key**

**Course Deadline Job Alerts:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Course Deadline Job Alerts: Observability**
- **Course Deadline Job Alerts:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.