from fastapi import APIRouter

from agents.db_fix_agent import DBFixAgent

from models.request import RCARequest


router = APIRouter(
    prefix="/api/v1",
    tags=["DB Fix Agent"]
)

agent = DBFixAgent()


@router.post("/execute")
def execute(request: RCARequest):

    return agent.execute(request)