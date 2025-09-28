from .GenerateAPIClientBase import GenerateAPIClientBase

class GenerateAPIClientGenerate(GenerateAPIClientBase):
    name_of_api_providing_codeunit: str
    generated_program_part_name: str
    
    def __init__(self,name_of_api_providing_codeunit: str,generated_program_part_name: str):
        self.name_of_api_providing_codeunit=name_of_api_providing_codeunit
        self.generated_program_part_name=generated_program_part_name

    def generate_api_client(self)->bool:
        return True
