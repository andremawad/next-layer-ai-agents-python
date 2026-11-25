# The demo clinic (fictional)

Every episode uses the same made-up clinic, so the answers in the videos and the code agree. If you
change a fact, change it everywhere it appears (listed below).

## Opening hours

- Monday to Friday: 9:00 to 21:00
- Saturday: 10:00 to 16:00
- Closed on Sundays and public holidays

## Cancelling or moving a booking

- Free up to 24 hours before the appointment starts.
- Less than 24 hours before, including the same day: a fee of $50.
- A missed appointment without cancelling: a fee of $100, and the next booking needs a deposit.

## People and bookings

Patients `sara` and `adam`, doctors Dr. Lina and Dr. Omar, and bookings like `B-102` (Thursday
16:30). All names and numbers are invented.

## Where the facts live

- Ep04 `docs/opening-hours.md`, `docs/cancellation-policy.md` (the RAG documents)
- Ep05 `NOTES` in `vector_store.py`
- Ep09 `SYSTEM` prompt in `voice_agent.py`
- Ep10 specialist prompts in `multi_agent.py`
- Ep11 `HOURS` and `POLICY` in `clinic_server.py`
