from datetime import datetime
import pytz
from sqlalchemy import select
 
from app.tasks.scheduler import scheduler
from app.core.database import async_session_maker
from app.models.models import Election, ElectionEvent
from app.services.results import calculate_election_winner
 
IST = pytz.timezone("Asia/Kolkata")
 
 
async def auto_complete_and_calculate():
    async with async_session_maker() as db:
        now = datetime.now(IST).replace(tzinfo=None)
        print("RESULT CRON RUN AT:", now)
 
        elections = (
            await db.execute(
                select(Election)
                .join(ElectionEvent)
                .where(
                    ElectionEvent.voting_end <= now,
                    Election.result_calculated == False,
                )
            )
        ).scalars().all()
 
        for election in elections:
            await calculate_election_winner(db, election.election_id)
 
 
def start_result_scheduler():
    scheduler.add_job(
        auto_complete_and_calculate,
        "interval",
        minutes=1,
        id="result_job",
        replace_existing=True,
    )
 