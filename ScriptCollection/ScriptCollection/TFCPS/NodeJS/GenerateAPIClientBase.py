from abc import ABC, abstractmethod


class GenerateAPIClientBase(ABC):

    @abstractmethod
    def generate_api_client(self)->bool:
        raise ValueError("Method is abstract")
