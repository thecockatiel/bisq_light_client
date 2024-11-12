from pathlib import Path
import shutil
from datetime import datetime

from bisq.logging import get_logger

logger = get_logger(__name__)

def rolling_backup(dir_path: str, file_name: str, num_max_backup_files: int) -> None:
    dir_obj = Path(dir_path)
    
    if dir_obj.exists():
        backup_dir = dir_obj.joinpath("backup")
        
        if not backup_dir.exists():
            if not backup_dir.mkdir(exist_ok=True):
                logger.warning("make dir failed.\nBackupDir=" + str(backup_dir))
        
        orig_file = dir_obj.joinpath(file_name)
        
        if orig_file.exists():
            dir_name = f"backups_{file_name}"
            dir_name = dir_name.replace(".", "_")
            
            backup_file_dir = backup_dir.joinpath(dir_name)
            
            if not backup_file_dir.exists():
                if not backup_file_dir.mkdir(exist_ok=True):
                    logger.warning("make backupFileDir failed.\nBackupFileDir=" + str(backup_file_dir))
            
            backup_file = backup_file_dir.joinpath(f"{datetime.now().timestamp()}_{file_name}") 
            
            try:
                shutil.copy(str(orig_file), str(backup_file))
                
                prune_backup(backup_file_dir, num_max_backup_files)
            except Exception as e:
                logger.error("Backup key failed: " + str(e))

def prune_backup(backup_dir_path: str, num_max_backup_files: int) -> None:
    backup_dir = Path(backup_dir_path)

    if backup_dir.is_dir():
        files = list(backup_dir.iterdir())
        
        if files:
            if len(files) > num_max_backup_files:
                files.sort(key=lambda x: x.name)
                file_to_delete = files[0]
                
                if file_to_delete.is_file():
                    if not file_to_delete.unlink(missing_ok=True):
                        logger.error("Failed to delete file: " + str(file_to_delete))
                    else:
                        prune_backup(backup_dir_path, num_max_backup_files)
                elif file_to_delete.is_dir():
                    prune_backup(str(file_to_delete), num_max_backup_files)

def does_file_contain_keyword(file_path: str, keyword: str) -> bool:
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if keyword in line:
                    return True
        return False
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error searching file {file_path}: {str(e)}")
        raise
