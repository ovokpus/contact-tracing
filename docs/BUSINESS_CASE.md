# Business case: SF App-Scan Contact Tracer

**Who was at the same place at about the same time, from venue check-ins in Elasticsearch.**

## Who buys this

The buyer is the safety lead at an organisation that already records check-ins at its own sites, such as a campus, hospital, event venue or large employer. The users are the safety or health team running an exposure lookup after an incident.

## The problem and what it costs

After an incident (an infection, a chemical exposure, a security event), the team needs to know who was nearby, fast. Doing this from raw check-in logs by hand takes hours. It is a search problem: filter by person, then by place and time window, then rank. Elasticsearch handles geo points and time ranges well. I found no reliable public figure for the cost of slow exposure lookups, so this case uses assumptions. **All data in the repo is synthetic.**

## How the repo solves it

| Need | What in the repo does it |
|---|---|
| Index check-ins | Elasticsearch with geo points, time ranges and full-text fields |
| Find contacts | `GET /devices/{id}/contacts?window_minutes=30`: the person's scans, then everyone at the same business within ±30 minutes, grouped by device with the shortest gap and repeat count |
| Map it | A React + Leaflet UI |
| Synthetic data | `tracer/synthetic.py` (Faker, fixed seed) generates people, devices, businesses and scans |
| Deploy | Terraform for Cloud Run, Azure Container Apps and AWS ECS |

## Use-case scenarios

All of these organisations are fictional.

1. **A university health office** checks which lab users shared a room with a confirmed case, using its own badge data.
2. **A hospital infection-control team** lists staff who were on a ward during a given shift.
3. **A conference organiser** finds which session attendees overlapped with someone who later reported an illness.

## ROI: a worked model (illustrative)

These figures are **illustrative assumptions** unless a source is linked.

| Input | Value | Basis |
|---|---|---|
| Exposure lookups a year | 30 | Assumption |
| Hours per lookup by hand | 4 | Assumption |
| Hours with the tool | 0.5 | Assumption |
| Analyst loaded cost an hour | US$60 | Assumption |

Saving: 30 × 3.5 h × $60 ≈ **US$6,300 a year**, plus faster notification, which is the real point.

## Path to production

1. Use only check-in data the organisation already collects, with a privacy impact assessment.
2. Restrict access, log every lookup and set short retention.
3. Load real check-ins through a controlled ingest job.

## Risks and limits

- Location tracing is sensitive. It needs a clear legal basis, consent and governance.
- Being at the same venue isn't proof of contact.

**Case strength:** **Weak to moderate.** The search technique is sound, but the money case is small and the privacy bar is high.

## Sources

No external statistics are used. All figures above are stated assumptions or come from the repo itself.
