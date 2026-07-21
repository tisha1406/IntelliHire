from app.repositories.base_repository import BaseRepository


class StrategyRepository(BaseRepository):

    def __init__(self):
        super().__init__("strategies")

    async def get_by_strategy_id(self, strategy_id: str):
        return await self.get_one(
            {"strategy_id": strategy_id}
        )