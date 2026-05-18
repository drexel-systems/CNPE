# Week 10 Lab Guide — Extension Implementation + Project Close

**Course:** CS 463 — Cloud Native Platform Engineering
**Week 10 — two sessions**
**Session 1 (80 min):** Lab 9 — Extension Implementation
**Session 2 (80 min):** Project working session — demo prep + WAF reflection
**Finals week:** No class — record final video, write reflection, submit
**AWS infrastructure required:** Yes — extending your Lab 6 stack
**Prerequisite:** Extension design doc committed to repo at `/8-CloudNative/extension-design.md`

---

## Before Session 1 — Three Checks

Do these before arriving. If any of them fail, fix it before session start — not during.

**Check 1 — Your design doc is in the repo.** Open `/8-CloudNative/extension-design.md`. It should have all six sections and be specific enough that someone else could implement it. If it is vague, tighten it now. Lab 9 is a build session, not a design session.

**Check 2 — Your Lab 6 stack deploys cleanly.** Run `pulumi up` from your Lab 6 directory. If it errors, fix it before arriving. Lab 9 adds code on top of a working Lab 6 — it cannot add on top of a broken one. If your stack was deployed and you destroyed it, redeploy it now and confirm all three core routes return expected status codes via Postman.

**Check 3 — Your Postman collection runs cleanly.** Run the full collection against your deployed stack. All three core routes should pass. If anything fails, that is a Lab 6 bug that needs fixing before Lab 9 adds more complexity on top of it.

If Check 2 or Check 3 is failing when you arrive, go directly to the instructor or a TA. There is no version of Lab 9 that works without a working Lab 6 underneath.

---

## Session 1 — Lab 9: Extension Implementation (80 min)

### Strategy: Build in Slices

Do not write your entire extension and then run `pulumi up` once. Build in slices — deploy after each slice, confirm it works, then add the next. This is the same pattern from Labs 5 and 6.

**For route-based extensions** (PATCH, DELETE, status filtering, pagination):

- **Slice A — Pulumi first.** Update `__main__.py` to add any new resources or permissions (e.g., `dynamodb:UpdateItem` for PATCH, a GSI for status filtering). Add the new route to API Gateway if needed. Run `pulumi up`. Confirm the new route exists in the console even if it returns 500 — you just need the wiring in place before adding the handler logic.
- **Slice B — Handler logic.** Add the function to your handler file. Run `pulumi up` again (Pulumi re-packages the Lambda). Hit the new route with `curl` to confirm basic routing.
- **Slice C — Test edge cases.** Add the new Postman requests. Run success case, then failure cases (404 on missing ID, 400 on invalid input). Fix anything that fails.

**For integration extensions** (SNS, authorizer):

- **Slice A — New resource only.** Add the SNS topic or authorizer Lambda as a Pulumi resource with stub behavior. Deploy and confirm the resource exists in AWS.
- **Slice B — Wire it.** Connect the existing pipeline to the new resource (publish to SNS on order receipt, attach the authorizer to API Gateway). Deploy.
- **Slice C — End-to-end test.** Confirm the extension fires correctly. For SNS: confirm the subscriber receives the notification. For authorizer: confirm a valid token succeeds and an invalid token returns 401.

### Definition of Done

| Extension | Done when... |
|-----------|-------------|
| `PATCH /orders/{id}` | PATCH to valid ID returns 200 with updated record; PATCH to missing ID returns 404; invalid status value returns 400; GET after PATCH shows updated status in DynamoDB |
| `DELETE /orders/{id}` | DELETE to valid ID returns 204; record still exists in DynamoDB with `status: cancelled`; DELETE on already-cancelled order returns 204 (idempotent) |
| Status filtering | `GET /orders?status=received` returns only matching orders; `GET /orders` with no filter returns everything; unrecognized status returns 200 with empty list |
| Customer scoping | `POST /orders` stores `customer_id` in DynamoDB; `GET /orders?customer_id=X` returns only that customer's orders; `GET /orders` with no filter returns all orders (internal/admin behavior); `GET /orders?customer_id=unknown` returns 200 with empty list |
| Pagination | `GET /orders?limit=5` returns ≤5 orders + `next_cursor` token; passing `?cursor=...` returns the next page; last page has no `next_cursor` |
| SNS notifications | `POST /orders` triggers an SNS publish; subscriber shows the notification (CloudWatch log or email) |
| Lambda authorizer | Request with valid token succeeds; request with missing/invalid token returns 401; authorizer Lambda log shows the validation decision |

### Common Pitfalls

**Missing IAM permission.** If a new DynamoDB operation (e.g., `UpdateItem` for PATCH, `Query` for GSI filtering) returns `AccessDeniedException` in CloudWatch Logs, your execution role is missing the permission. Go back to `__main__.py` and add it.

**Stale Postman environment variable.** If you destroyed and redeployed your stack, `api_url` in Postman may point at the old endpoint. Run `pulumi stack output orders_url` and update the environment variable.

**DynamoDB Decimal serialization.** If PATCH or DELETE returns a response body and that body includes numeric fields from DynamoDB, you may hit the same `Decimal` serialization error from Lab 6. Wrap the response in `json.dumps(item, cls=DecimalEncoder)`.

**Lambda package size.** If you are adding a new Python dependency (e.g., a JWT library for the authorizer), the deployment package may exceed Lambda's inline limit. The existing `requirements.txt` and Pulumi `Archive` configuration handles this — just add the dependency to `requirements.txt` and redeploy.

### Deliverables from Session 1

By the end of this session:

- [ ] Extension working end-to-end, tested with Postman
- [ ] `pulumi up` runs cleanly with new resources included
- [ ] Postman collection updated with new requests for the extension
- [ ] Take screenshot: Postman Runner output showing all requests passing, including the extension request(s) — this is **D2** in your final submission

---

## Session 2 — Project Working Session (80 min)

### Priority 1 — Capture the Demo Dry-Run (15 min)

Record a 60-second screen capture now. You need:

1. Terminal showing `pulumi stack output orders_url` (confirms what endpoint you're hitting)
2. Postman Runner executing the full collection — all three core routes plus the extension
3. All requests showing correct status codes (202, 200, 204 — whichever applies)

Use Loom, QuickTime (Mac), or Xbox Game Bar (Windows). Audio is not required for the dry-run — the final video needs narration, but this clip is visual proof.

**Why now, not finals week?** This is the segment most likely to fail under time pressure. Common failures: the stack was destroyed and not redeployed, the Postman environment variable is stale, the extension request was never added to the collection. Capturing it today surfaces all of those while the instructor is available. Doing it the night before the deadline with a problem is a very bad situation.

Save the recording. This rough cut becomes the Postman segment of your final demo video.

### Priority 2 — Assemble the WAF Reflection Draft (30 min)

Open your Week 8 lab deliverable — the six-pillar audit table and the W1/W2 paragraphs. These are the raw material for the 1–2 page WAF reflection. You are not writing the reflection from scratch — you are curating and synthesizing.

The reflection has three required components:

**Two pillars addressed well** — with specific code or configuration examples. Pull from your audit the two findings you classified as Best Practice Met or Conscious Tradeoff with the strongest evidence. For each, write 2–3 sentences: what you did, where it appears in your code, and why it matters.

Good: "I addressed the Reliability pillar by ensuring the processor Lambda re-raises exceptions on DynamoDB write failures rather than swallowing them. This means SQS retries the message rather than silently acknowledging a failed write — visible in `processor/handler.py` at the `put_item` call."

Weak: "I addressed Reliability by thinking about what happens when things fail."

**One pillar not addressed** — with a concrete proposed fix. Pull from your audit the Unknown Gap you named in W1. The fix should be specific enough to implement: not "add better security" but "configure a Dead Letter Queue on the SQS queue by adding `redrive_policy` to the queue resource in `__main__.py` with `maxReceiveCount=3`."

**One thing that worked differently than you expected.** This is the only component that is not directly from your Week 8 audit. Think back over the full build — Labs 2 through Lab 9. What genuinely surprised you? Common answers: the eventual consistency window was longer or shorter than expected; a Pulumi resource had unexpected behavior; the IAM permissions required more iteration than anticipated; the extension was harder or easier than the design doc suggested. Write 2–3 honest sentences.

> **Note on the extension:** If your extension closed a gap from your W1 audit, update the "one pillar not addressed" component to reflect what changed — or name a different gap that is still open. The reflection should reflect your architecture as it stands after Lab 9, not as it stood after Lab 6.

### Priority 3 — Run `pulumi destroy` and Confirm (10 min)

Run `pulumi destroy` at least once before the final recording. The demo includes showing a clean teardown. A `pulumi destroy` that hangs on a specific resource or errors halfway through is a bad final impression — and it is fixable now if you find it today.

### Priority 4 — Plan the Final Demo Video (25 min)

The demo is exactly 5 minutes. Over 5 minutes loses 5 points. Plan your segments:

| Segment | Target time | What to show |
|---------|-------------|-------------|
| `pulumi up` | ~60 sec | Terminal — clean deployment, all resources created, outputs shown |
| Postman collection run | ~90 sec | Use the dry-run recording from Priority 1 as the base. All core routes + extension. |
| Architecture walkthrough | ~60 sec | Draw or display a diagram. Name each component and its role. Note that API Gateway, Lambda, SQS, and DynamoDB are AWS-managed services outside the VPC — the VPC contains the EC2 bastion for admin access only. |
| One architectural decision | ~45 sec | Pick one: why async? why SQS over synchronous? why this partition key? why this extension? Explain it in plain language. |
| `pulumi destroy` | ~45 sec | Terminal — clean teardown. |

Narrate throughout. The grader is watching a video of a system they cannot touch — your narration is what connects the components to the architecture.

Record the final demo during finals week when everything is polished. But if you want to do a full practice run today, use the remaining time.

---

## Finals Week — Final Submission

No class this week. Three things to do, in order.

### 1 — Record the final demo video

Use your Week 10 Session 2 dry-run as the Postman segment. Add the `pulumi up` intro, the architecture walkthrough, the decision explanation, and the `pulumi destroy` outro. Keep it under 5 minutes.

Upload to YouTube (unlisted is fine) or Loom. Copy the link.

### 2 — Finalize the written WAF reflection

Polish the draft you assembled in Session 2. Target is 1–2 pages — not a sentence longer than necessary. The three components must be present. Cite specific file locations and configuration values where you claim evidence.

Export as a PDF.

### 3 — Submit everything

| What | Where |
|------|-------|
| Demo video link (YouTube or Loom) | Canvas — Course Project assignment |
| WAF reflection PDF | Canvas — Course Project assignment |
| Pulumi code + all lab deliverables | GitHub repo — pushed before deadline |

**No late submissions on the course project under any circumstances.** The grading window during finals week is tight. Submissions after the deadline cannot be graded in time for final grade submission.

---

## Full Lab 9 Deliverables

Submitted as a PDF to Canvas:

- [ ] **D1 — `pulumi up` output** showing new extension resources deploying cleanly (15 pts)
- [ ] **D2 — Postman Runner screenshot** showing all requests passing including the extension (25 pts)
- [ ] **D3 — Extension code** committed to repo: `__main__.py` diff + handler changes + any new files (30 pts)
- [ ] **D4 — 60-second dry-run video** link showing Postman Runner against the live stack (10 pts)
- [ ] **W1 — Revised WAF paragraph** — 1 paragraph acknowledging what the extension does or doesn't fix relative to the W1 gap you named in Week 8 (20 pts). If you implemented customer scoping: note that the extension provides the data model for multi-tenant access control but does not implement authentication — in production, `customer_id` would be derived from a verified JWT token rather than accepted as a caller-supplied parameter. That is the remaining Security gap to name.

**Total: 100 points.**

---

## Course Project Final Checklist

Use this before submitting.

**Working API (GitHub repo):**
- [ ] `POST /orders` → 202 Accepted
- [ ] `GET /orders/{id}` → 200 / 404
- [ ] `GET /orders` → 200
- [ ] At least one extension working end-to-end
- [ ] `pulumi up` runs cleanly from a fresh state
- [ ] `pulumi destroy` runs cleanly
- [ ] No manually created resources

**Demo video (Canvas link):**
- [ ] Under 5 minutes
- [ ] `pulumi up` shown completing
- [ ] Postman run showing all core routes + extension
- [ ] Architecture walkthrough with narration
- [ ] One architectural decision explained
- [ ] `pulumi destroy` shown completing

**WAF reflection (Canvas PDF):**
- [ ] Two pillars addressed well with specific code/config evidence
- [ ] One pillar not addressed with a concrete proposed fix
- [ ] One genuine surprise from the build
- [ ] 1–2 pages — not longer
