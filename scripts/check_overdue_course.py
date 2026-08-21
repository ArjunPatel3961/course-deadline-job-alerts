"""Send one overdue course job through the local service."""

import json
import urllib.request
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc).replace(microsecond=0)

payload = {
    "job_id": "delivery-2026-08-21-algebra",
    "course_id": "algebra-101",
    "learner_id": "learner-42",
    "educator_id": "educator-7",
    "scheduled_for": (now - timedelta(hours=2)).isoformat(),
    "learner_deadline": (now - timedelta(hours=1)).isoformat(),
    "delivered_at": None,
}
request = urllib.request.Request(
    "http://127.0.0.1:8000/scheduled-jobs/run",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request) as response:
    print(json.dumps(json.load(response), indent=2))
