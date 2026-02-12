from datetime import datetime
import pytz
from sqlalchemy import update
 
from app.models.models import Election, ElectionEvent
from app.core.database import async_session_maker
 
IST = pytz.timezone("Asia/Kolkata")
 
 
async def update_election_status(db):
    now = datetime.now(IST).replace(tzinfo=None)
    print("STATUS CRON RUN AT:", now)
 
    # NOMINATION OPEN
    await db.execute(
        update(Election)
        .where(
            Election.event_id == ElectionEvent.event_id,
            ElectionEvent.nomination_start <= now,
            ElectionEvent.nomination_end > now,
        )
        .values(status="NOMINATION_OPEN")
    )
 
    # READY FOR POLL
    await db.execute(
        update(Election)
        .where(
            Election.event_id == ElectionEvent.event_id,
            ElectionEvent.nomination_end <= now,
            ElectionEvent.voting_start > now,
        )
        .values(status="READY_FOR_POLL")
    )
 
    # VOTING ACTIVE
    await db.execute(
        update(Election)
        .where(
            Election.event_id == ElectionEvent.event_id,
            ElectionEvent.voting_start <= now,
            ElectionEvent.voting_end > now,
        )
        .values(status="ACTIVE")
    )
 
    # COMPLETED
    await db.execute(
        update(Election)
        .where(
            Election.event_id == ElectionEvent.event_id,
            ElectionEvent.voting_end <= now,
        )
        .values(status="COMPLETED")
    )
 
    await db.commit()
 
 
async def run_status_update():
    async with async_session_maker() as db:
        await update_election_status(db)
 