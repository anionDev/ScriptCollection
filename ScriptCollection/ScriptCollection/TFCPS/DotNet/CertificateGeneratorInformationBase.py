from abc import ABC


class CertificateGeneratorInformationBase(ABC):
    
    def generate_certificate(self)->bool:
        raise ValueError("Method is abstract")
