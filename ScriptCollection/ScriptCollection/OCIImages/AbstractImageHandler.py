from packaging.version import Version
from abc import ABC, abstractmethod

class AbstractImageHandler(ABC):
    
    @abstractmethod
    def can_handle(self,image_name:str)->bool:
        raise NotImplementedError()#because it is abstract
    
    def _protected_get_credentials_for_registry(self,registry_address:str,username_str:str)->tuple[str,str]:
        """return (username, password) for basic auth.
        Data will be taken from "~/.scriptcollection/GlobalCache/RegistryCredentials.csv" if available.
        If no credentials are available then None will be returned for the missing values."""
        raise NotImplementedError()#because it is abstract
    
    @abstractmethod
    def get_available_tags_of_image(image_name:str,registry_address:str)->list[str]:
        raise NotImplementedError()#because it is abstract

    @abstractmethod
    def tag_to_version(image_name:str,registry_address:str,tag:str)->Version:
        raise NotImplementedError()#because it is abstract

    @abstractmethod
    def version_to_tag(image_name:str,registry_address:str,version:Version)->str:
        raise NotImplementedError()#because it is abstract
