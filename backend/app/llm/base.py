from abc import ABC, abstractmethod

from app.schemas import LookupExplanation


class LLMProvider(ABC):
    name: str
    model_name: str

    @abstractmethod
    async def explain(self, text: str) -> LookupExplanation:
        raise NotImplementedError
