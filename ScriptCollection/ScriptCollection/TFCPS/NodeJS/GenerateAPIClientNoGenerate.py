from .GenerateAPIClientBase import GenerateAPIClientBase


class GenerateAPIClientNoGenerate(GenerateAPIClientBase):

    def generate_api_client(self)->bool:
        return False
