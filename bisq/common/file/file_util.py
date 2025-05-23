import os
from pathlib import Path
import platform
import shutil
from datetime import datetime
import tempfile
from typing import Optional, Union

from bisq.common.file.resource_not_found_exception import ResourceNotFoundException
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.resources import p2p_resource_dir
from utils.java_compat import java_cmp_str


def unlink(path: Path):
    if path.is_file():
        try:
            path.unlink(missing_ok=True)
            return True
        except Exception as e:
            return False
    else:
        try:
            path.rmdir()
            return True
        except Exception as e:
            return False

def rolling_backup(dir_path: Path, file_name: str, num_max_backup_files: int) -> None:
    
    if dir_path.exists():
        backup_dir = dir_path.joinpath("backup")
        
        if not backup_dir.exists():
            try:
                backup_dir.mkdir(parents=True, exist_ok=True)
            except:
                pass
            if not backup_dir.exists():
                logger = get_ctx_logger(__name__)
                logger.warning("make dir failed.\nBackupDir=" + str(backup_dir))
        
        orig_file = dir_path.joinpath(file_name)
        
        if orig_file.exists():
            dir_name = f"backups_{file_name}"
            dir_name = dir_name.replace(".", "_")
            
            backup_file_dir = backup_dir.joinpath(dir_name)
            
            if not backup_file_dir.exists():
                try:
                    backup_file_dir.mkdir(parents=True, exist_ok=True)
                except:
                    pass
                if not backup_file_dir.exists():
                    logger = get_ctx_logger(__name__)
                    logger.warning("make backupFileDir failed.\nBackupFileDir=" + str(backup_file_dir))
            
            backup_file = backup_file_dir.joinpath(f"{datetime.now().timestamp()}_{file_name}") 
            
            try:
                # Path supported on python 3.8+
                shutil.copy(orig_file, backup_file)
                
                prune_backup(backup_file_dir, num_max_backup_files)
            except Exception as e:
                logger.error("Backup key failed: " + str(e))

def prune_backup(backup_dir_path: Path, num_max_backup_files: int) -> None:
    if backup_dir_path.is_dir():
        files = list(backup_dir_path.iterdir())
        
        if files:
            if len(files) > num_max_backup_files:
                files.sort(key=lambda x: java_cmp_str(x.name))
                file_to_delete = files[0]
                
                if file_to_delete.is_file():
                    try:
                        unlink(file_to_delete)
                        deleted = True
                    except:
                        deleted = False
                    if not deleted:
                        logger = get_ctx_logger(__name__)
                        logger.error("Failed to delete file: " + str(file_to_delete))
                    else:
                        prune_backup(backup_dir_path, num_max_backup_files)
                elif file_to_delete.is_dir():
                    prune_backup(file_to_delete, num_max_backup_files)

def delete_directory(dir_path: Path, exclude: Optional[Path] = None, ignore_locked_files: bool = True) -> None:
    exclude_file_found = False
    if dir_path.is_dir():
        for item in dir_path.iterdir():
            exclude_file_found_local = exclude is not None and item.resolve() == exclude.resolve()
            exclude_file_found |= exclude_file_found_local
            if not exclude_file_found_local:
                delete_directory(item, exclude, ignore_locked_files)
    # Finally delete main file/dir if exclude file was not found in directory
    if not exclude_file_found and not (exclude is not None and dir_path.resolve() == exclude.resolve()):
        try:
            delete_file_if_exists(dir_path, ignore_locked_files)
        except Exception as e:
            logger = get_ctx_logger(__name__)
            logger.error(f"Could not delete file. Error={str(e)}")
            raise IOError(e)

def delete_file_if_exists(file: Path, ignore_locked_files = True) -> None:
    try:
        if platform.system().lower() == "windows":
            file = file.resolve()

        if file.exists() and not unlink(file):
            if ignore_locked_files:
                # We check if file is locked. On Windows all open files are locked by the OS
                if is_file_locked(file):
                    logger = get_ctx_logger(__name__)
                    logger.info(f"Failed to delete locked file: {file.absolute()}")
            else:
                message = f"Failed to delete file: {file.absolute()}"
                raise IOError(message)
    except Exception as e:
        logger = get_ctx_logger(__name__)
        logger.error(str(e), exc_info=e)
        if isinstance(e, IOError):
            raise e
        raise IOError(e)

def is_file_locked(file: Path) -> bool:
    try:
        if file.exists():
            with open(file, 'a'):
                return False
        else:
            return False
    except:
        return True

def does_file_contain_keyword(file_path: Path, keyword: str) -> bool:
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if keyword in line:
                    return True
        return False
    except FileNotFoundError:
        logger = get_ctx_logger(__name__)
        logger.error(f"File not found: {str(file_path)}")
        raise
    except Exception as e:
        logger = get_ctx_logger(__name__)
        logger.error(f"Error searching file {str(file_path)}: {str(e)}")
        raise
    
def rename_file(file: Path, new_file: Path) -> None:
    if file == new_file: return
    
    canonical = new_file.resolve()
    try:
        # Work around an issue on Windows whereby you can't rename over existing files.
        if (platform.system().lower() == "windows" and canonical.exists()):
            unlink(canonical)
        file.rename(canonical)
    except Exception as e:
        logger = get_ctx_logger(__name__)
        logger.error(f"Failed to rename {file} to {new_file}: {str(e)}")
        raise

def remove_and_backup_file(db_dir: Path, storate_file: Path, file_name: str, backup_folder_name: str):
    corrupted_backup_dir = db_dir.joinpath(backup_folder_name)
    if not corrupted_backup_dir.exists():
        try:
            corrupted_backup_dir.mkdir(parents=True, exist_ok=True)
        except:
            logger = get_ctx_logger(__name__)
            logger.error(f"Failed to create corrupted backup dir: {corrupted_backup_dir}")
        return
    corrupted_file = corrupted_backup_dir.joinpath(file_name)
    if corrupted_file.exists():
        rename_file(storate_file, corrupted_file)

def create_new_file(path: Path):
    path.touch(exist_ok=False)
    return path

def create_temp_file(prefix: Optional[str] = None, suffix: Optional[str] = None, dir: Optional[Path] = None):
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=dir)
    os.close(fd)
    return Path(path)

def p2p_resource_to_file(resource_path: Union[str, Path], destination_path: Path):
    from_path = p2p_resource_dir.joinpath(resource_path)
    if not from_path.exists():
        raise ResourceNotFoundException(str(from_path))
    return shutil.copy(from_path, destination_path)

def p2p_list_resource_directory(dir_name: str):
    path = p2p_resource_dir.joinpath(dir_name)
    if not path.exists():
        return []
    return os.listdir(p2p_resource_dir.joinpath(dir_name))

def get_usable_space(path: Path) -> int:
    try:
        return shutil.disk_usage(path).free
    except Exception as e:
        logger = get_ctx_logger(__name__)
        logger.error(f"Failed to get usable space for {path}: {str(e)}")
        return 0
