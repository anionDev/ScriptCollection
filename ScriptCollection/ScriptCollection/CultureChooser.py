import re
from .GeneralUtilities import GeneralUtilities

class CultureChooser:
    __culture_regex = re.compile(r"^[a-zA-Z]+(-[a-zA-Z]+)?$")

    def is_valid_culture(self,culture_string: str) -> bool:
        """
        Checks if a string is in a valid language/culture format.
        result:
        de, de-DE, en, en-US, fr, fr-FR, etc. is allowed.
        de3, zh-Hans-CN, en_US, etc. is not allowed.
        """
        return bool(self.__culture_regex.fullmatch(culture_string)) 

    def get_index_html(self,site_title:str) -> str:
        content = GeneralUtilities._internal_load_resource("CultureChooser/index.html")
        content_as_string = content.decode("utf-8")
        result=GeneralUtilities.replace_variable("<!--","title","-->", site_title, content_as_string)
        return result
    
    def get_culture_chooser_script(self,supported_languages:list[str]) -> str:
        GeneralUtilities.assert_condition("en" in supported_languages, "The default language 'en' must be included in the list of supported languages.")
        for supported_language in supported_languages:
            GeneralUtilities.assert_condition(self.is_valid_culture(supported_language), f"Invalid language code '{supported_language}'. Supported languages must be in the format 'en' or 'en-US'.") 
        content = GeneralUtilities._internal_load_resource("CultureChooser/CultureChooser.js")
        content_as_string = content.decode("utf-8")
        result=GeneralUtilities.replace_variable("/*","supportedCultures","*/", ", ".join([f"\"{supported_language}\"" for supported_language in supported_languages]), content_as_string)
        return result
