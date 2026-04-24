from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

class OCRRunnerInformation(ABC):

    @abstractmethod
    def accept(self,visitor:OCRRunnerInformationVisitor)->None:
        raise ValueError("This method must be implemented by the concrete subclasses.")

    @abstractmethod
    def accept(self,visitor:OCRRunnerInformationVisitor[T])->T:
        raise ValueError("This method must be implemented by the concrete subclasses.")

    # ---------------------------

class OCRRunnerInformationRemoteServer(OCRRunnerInformation):

    def accept(self,visitor:OCRRunnerInformationVisitor)->None:
        visitor.handle(self)

    def accept(self,visitor:OCRRunnerInformationVisitor[T])->T:
        return visitor.handle(self)
    

class OCRRunnerInformationLocalServerUsingDocker(OCRRunnerInformation):

    def accept(self,visitor:OCRRunnerInformationVisitor)->None:
        visitor.handle(self)

    def accept(self,visitor:OCRRunnerInformationVisitorT[T])->T:
        return visitor.handle(self)

class OCRRunnerInformationLocalCLI(OCRRunnerInformation):

    def accept(self,visitor:OCRRunnerInformationVisitor)->None:
        visitor.handle(self)

    def accept(self,visitor:OCRRunnerInformationVisitorT[T])->T:
        return visitor.handle(self)
    
# ---------------------------

class OCRRunnerInformationVisitor(ABC):
    
    @abstractmethod
    def handle(self,ocrRunnerInformation:OCRRunnerInformationRemoteServer) -> None:
        raise ValueError("This method must be implemented by the concrete subclasses.")
    
    @abstractmethod
    def handle(self,ocrRunnerInformation:OCRRunnerInformationLocalServerUsingDocker) -> None:
        raise ValueError("This method must be implemented by the concrete subclasses.")
    
    @abstractmethod
    def handle(self,ocrRunnerInformation:OCRRunnerInformationLocalCLI) -> None:
        raise ValueError("This method must be implemented by the concrete subclasses.")

class OCRRunnerInformationVisitorT(ABC, Generic[T]):
    
    @abstractmethod
    def handle(self,ocrRunnerInformation:OCRRunnerInformationRemoteServer) -> T:
        raise ValueError("This method must be implemented by the concrete subclasses.")
    
    @abstractmethod
    def handle(self,ocrRunnerInformation:OCRRunnerInformationLocalServerUsingDocker) -> T:
        raise ValueError("This method must be implemented by the concrete subclasses.")
    
    @abstractmethod
    def handle(self,ocrRunnerInformation:OCRRunnerInformationLocalCLI) -> T:
        raise ValueError("This method must be implemented by the concrete subclasses.")

class OCRRunnerInformationUtilities:
    @abstractmethod
    def load_from_settings(self) -> OCRRunnerInformation:
        pass#TODO load from ~/.ScriptCollection/OCRRunner/Settings.txt"
