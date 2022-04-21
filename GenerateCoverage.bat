coverage run -m pytest
coverage xml
reportgenerator -reports:coverage.xml -targetdir:TestCoverage -reporttypes:Badges