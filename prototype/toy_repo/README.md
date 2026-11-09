# Demo student portal (fictional)

A small, fictional application used only to demonstrate the triage prototype's draft pull
requests. It contains four planted bugs, one for each pilot cause that is fixed by a code change:

| Cause | File | Bug |
|---|---|---|
| C01 Slow external service, outbound call has no timeout | `portal/payments.py` | The bank gateway call has no timeout |
| C04 Repeated queries per request (N+1) | `portal/results.py` | One query per student when building class results |
| C05 Cache failing silently | `portal/cache.py` | Values with dates cannot be serialised; the failure is only logged |
| C08 Sign-in writes collide on the user row | `portal/auth.py` | The refresh token is written to the user row inside the sign-in transaction |

`python -m pytest` shows one failing test per planted bug. No real system, data or people.
Pull requests on this repository are drafts opened by the triage prototype; a person reviews them.
