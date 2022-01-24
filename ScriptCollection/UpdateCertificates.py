import os
from pathlib import Path
import traceback
from shutil import copyfile
from .Core import ScriptCollectionCore
from .Utilities import GeneralUtilities

class CertificateUpdater:

    domains:list(str)
    email:str

    current_folder = os.path.dirname(os.path.abspath(__file__))
    repository_folder = GeneralUtilities.resolve_relative_path(f"..{os.path.sep}..{os.path.sep}..{os.path.sep}", current_folder)
    letsencrypt_folder = GeneralUtilities.resolve_relative_path(f"..{os.path.sep}..{os.path.sep}Volumes{os.path.sep}letsencrypt", current_folder)
    letsencrypt_live_folder = os.path.join(letsencrypt_folder, "live")
    letsencrypt_archive_folder = os.path.join(letsencrypt_folder, "archive")
    log_folder = GeneralUtilities.resolve_relative_path(f"Logs{os.path.sep}Overhead", repository_folder)
    sc = ScriptCollectionCore()
    line = "___________________________________________________________________"

    def __init__(self, domains:list(str), email:str):
        self.domains=domains
        self.email = email


    def __get_latest_index_by_domain(self,domain: str) -> int:
        result= self.__get_latest_index_by_filelist(GeneralUtilities.get_all_files_of_folder(os.path.join(self.letsencrypt_archive_folder, domain)))
        GeneralUtilities.write_message_to_stdout(f"Debug: Latest found existing number for domain {domain}: {result}")
        return result

    def __get_latest_index_by_filelist(self,filenames:list) -> int:
        print("files:")
        print(filenames)
        filenames=[Path(os.path.basename(file)).stem for file in filenames]
        print(filenames)
        filenames=[file for file in filenames if file.startswith("privkey")]
        print(filenames)
        numbers = [int(file[len("privkey"):]) for file in filenames]
        #numbers=[]
        #print([os.path.basename(file) for file in filenames])
        result=max(numbers)
        return result


    def __replace_symlink_by_file(self,domain: str, filename: str, index: int) -> None:
        # ".../live/example.com/cert.pem" is a symlink but should replaced by a copy of ".../archive/example.com/cert.42pem"
        archive_file = os.path.join(self.letsencrypt_archive_folder, domain, filename+str(index)+".pem")
        live_folder = os.path.join(self.letsencrypt_live_folder, domain)
        live_filename = filename+".pem"
        live_file = os.path.join(live_folder, live_filename)
        self.sc.start_program_synchronously("rm", live_filename, live_folder, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)
        copyfile(archive_file, live_file)


    def __replace_file_by_symlink(self,domain: str, filename: str, index: int) -> None:
        # new ".../live/example.com/cert.pem" is a file but should replaced by a symlink which points to ".../archive/example.com/cert42.pem"
        live_folder = os.path.join(self.letsencrypt_live_folder, domain)
        live_filename = filename+".pem"
        self.sc.start_program_synchronously("rm", live_filename, live_folder, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)
        self.sc.start_program_synchronously("ln", f"-s ../../archive/{domain}/{filename+str(index)}.pem {live_filename}", live_folder,
                                    prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)


    def __replace_symlinks_by_files(self,domain):
        index = self.__get_latest_index_by_domain(domain)
        self.__replace_symlink_by_file(domain, "cert", index)
        self.__replace_symlink_by_file(domain, "chain", index)
        self.__replace_symlink_by_file(domain, "fullchain", index)
        self.__replace_symlink_by_file(domain, "privkey", index)


    def __replace_files_by_symlinks(self,domain):
        index = self.__get_latest_index_by_domain(domain)
        self.__replace_file_by_symlink(domain, "cert", index)
        self.__replace_file_by_symlink(domain, "chain", index)
        self.__replace_file_by_symlink(domain, "fullchain", index)
        self.__replace_file_by_symlink(domain, "privkey", index)


    def update_certificate_managed_by_docker_and_letsencrypt(self) -> None:
        GeneralUtilities.write_message_to_stdout("current_folder:")
        GeneralUtilities.write_message_to_stdout(self.current_folder)
        GeneralUtilities.write_message_to_stdout("letsencrypt_folder:")
        GeneralUtilities.write_message_to_stdout(self.letsencrypt_folder)
        GeneralUtilities.write_message_to_stdout("letsencrypt_live_folder:")
        GeneralUtilities.write_message_to_stdout(self.letsencrypt_live_folder)
        GeneralUtilities.write_message_to_stdout("letsencrypt_archive_folder:")
        GeneralUtilities.write_message_to_stdout(self.letsencrypt_archive_folder)
        GeneralUtilities.write_message_to_stdout("log_folder:")
        GeneralUtilities.write_message_to_stdout(self.log_folder)

        GeneralUtilities.write_message_to_stdout(self.line+self.line)
        GeneralUtilities.write_message_to_stdout("Updating certificates")
        self.sc.git_commit(self.current_folder, "Saved current changes")
        for domain in self.domains:
            try:
                GeneralUtilities.write_message_to_stdout(self.line)
                GeneralUtilities.write_message_to_stdout(f"Process domain {domain}")
                certificate_for_domain_already_exists = os.path.isfile(f"{self.letsencrypt_folder}/renewal/{domain}.conf")
                if certificate_for_domain_already_exists:
                    GeneralUtilities.write_message_to_stdout(f"Update certificate for domain {domain}")
                    self.__replace_files_by_symlinks(domain)
                else:
                    GeneralUtilities.write_message_to_stdout(f"Create certificate for domain {domain}")
                certbot_container_name = "r2_updatecertificates_certbot"
                dockerargument = f"run --name {certbot_container_name} --volume {self.letsencrypt_folder}:/etc/letsencrypt"
                dockerargument = dockerargument+f" --volume {self.log_folder}:/var/log/letsencrypt -p 80:80 certbot/certbot:latest"
                certbotargument = f"--standalone --email {self.email} --agree-tos --force-renewal --rsa-key-size 4096 --non-interactive --no-eff-email --domain {domain}"
                if(certificate_for_domain_already_exists):
                    self.sc.start_program_synchronously("docker", f"{dockerargument} certonly --no-random-sleep-on-renew {certbotargument}",
                                                self.current_folder, throw_exception_if_exitcode_is_not_zero=True)
                    self.__replace_symlinks_by_files(domain)
                else:
                    self.sc.start_program_synchronously("docker", f"{dockerargument} certonly --cert-name {domain} {certbotargument}",
                                                self.current_folder, throw_exception_if_exitcode_is_not_zero=True)
            except Exception as exception:
                GeneralUtilities.write_exception_to_stderr_with_traceback(exception, traceback, "Error while updating certificate")
            finally:
                try:
                    self.sc.start_program_synchronously("docker", f"container rm {certbot_container_name}", self.current_folder, throw_exception_if_exitcode_is_not_zero=True)
                except Exception as exception:
                    GeneralUtilities.write_exception_to_stderr_with_traceback(exception, traceback, "Error while removing container")

        GeneralUtilities.write_message_to_stdout("Commit changes...")
        self.sc.git_commit(self.repository_folder, "Executed certificate-update-process")
        GeneralUtilities.write_message_to_stdout("Finished certificate-update-process")
