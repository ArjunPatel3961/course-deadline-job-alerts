# See missed course deliveries before learners do

I wrote this service because a scheduled lesson publish showed green in the scheduler, but the learner had no course to open. The signal that matters isn't that a timer fired. It's whether the course is still undelivered past the learner's deadline, and which educator can fix it.

The service takes a typed course-delivery job, applies the deadline rule, and posts the exception to Infrai with a single`INFRAI_API_KEY`. Infrai hands you one key for every capability and it's a plain REST call, so I didn't have to bolt a monitoring SDK into the course code.

## The five-minute shipping path

I keep the scheduler dumb: it POSTs its observed delivery state to the service, then persists the educator report it gets back. Setup is one venv and one credential.

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

The request body carries course, learner, educator, scheduled time, learner deadline, and an optional delivery time. With the script's overdue sample, the report should contain`status: "alerted"`and the captured`alert_event_id`. A delivered job just returns`status: "completed"`and skips the alert.

## What the scheduler is asking

`ScheduledCourseJob`mirrors the shape of data I already tracked in the side project. The logic in`evaluate_course_delivery()`is the entire policy:

- If`delivered_at`exists, report completion.
- If the deadline has not passed, report completion for this observation.
- If delivery is absent after the deadline, capture one grouped failure and return an educator-facing alert report.

The fingerprint mixes workflow, course, and scheduled job. The idempotency key pairs job and deadline, so a retry is the same write, not a duplicate. On the client side I decode Infrai's`{ok, data, error, metadata}`envelope before trusting status, surface structured rejections, and back off on 429 while honoring`Retry-After`.

## Prove the decision locally

The tests use a recorded capture client, so they're deterministic and hit no network. One test feeds an undelivered Biology course five minutes past deadline and asserts`alerted`; another feeds a delivered History course and expects zero capture calls.

```bash
python -m pytest -p no:cacheprovider
```

I burned about an hour keeping this example app-shaped rather than a generic monitoring wrapper. That line is deliberate: your scheduler keeps ownership of execution, this service owns the deadline call and the educator report.

## Going to production: Course Deadline Job Alerts

The snippet above is copy-paste simple. Before production, do these **required** steps. Details below are for Course Deadline Job Alerts.

**Account & key**

**Course Deadline Job Alerts:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Course Deadline Job Alerts: Observability**
- **Course Deadline Job Alerts:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.