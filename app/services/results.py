from sqlalchemy import select, func, update
from app.models.models import Election, Candidate, Vote


async def calculate_election_winner(db, election_id: int):
    election = await db.get(Election, election_id)
    if not election:
        return {"error": "Election not found"}

    # stop duplicate calculation
    if election.total_votes > 0:
        return {"message": "Result already calculated"}

    vote_counts = (
        await db.execute(
            select(Vote.candidate_id, func.count(Vote.vote_id))
            .where(Vote.election_id == election_id)
            .group_by(Vote.candidate_id)
        )
    ).all()

    if not vote_counts:
        return {"error": "No votes found"}

    # reset
    await db.execute(
        update(Candidate)
        .where(Candidate.election_id == election_id)
        .values(vote_count=0, is_winner=False)
    )

    max_votes = max(count for _, count in vote_counts)
    winners = []

    for candidate_id, count in vote_counts:
        await db.execute(
            update(Candidate)
            .where(Candidate.candidate_id == candidate_id)
            .values(
                vote_count=count,
                is_winner=(count == max_votes),
            )
        )
        if count == max_votes:
            winners.append(candidate_id)

    total_votes = sum(count for _, count in vote_counts)

    election.total_votes = total_votes
    election.status = "COMPLETED"

    await db.commit()

    return {
        "message": "Winner calculated",
        "winners": winners,
        "total_votes": total_votes,
    }