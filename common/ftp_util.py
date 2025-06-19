import os
import logging
import ftplib
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class FTPClient:
    """FTP 클라이언트 클래스"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 21):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.ftp = None
    
    def connect(self) -> bool:
        """FTP 서버에 연결합니다."""
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port)
            self.ftp.login(self.username, self.password)
            logger.info(f"FTP 연결 성공: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"FTP 연결 실패: {self.host}:{self.port}, 오류: {e}")
            return False
    
    def disconnect(self):
        """FTP 연결을 종료합니다."""
        if self.ftp:
            try:
                self.ftp.quit()
                logger.info("FTP 연결 종료")
            except Exception as e:
                logger.warning(f"FTP 연결 종료 중 오류: {e}")
            finally:
                self.ftp = None
    
    def download_file(self, remote_file: str, local_file: str) -> bool:
        """파일을 다운로드합니다."""
        if not self.ftp:
            logger.error("FTP 연결이 없습니다.")
            return False
        
        try:
            # 로컬 디렉토리 생성
            os.makedirs(os.path.dirname(local_file), exist_ok=True)
            
            # 파일 다운로드
            with open(local_file, 'wb') as file:
                self.ftp.retrbinary(f'RETR {remote_file}', file.write)
            
            logger.info(f"파일 다운로드 완료: {remote_file} -> {local_file}")
            return True
            
        except Exception as e:
            logger.error(f"파일 다운로드 실패: {remote_file}, 오류: {e}")
            return False
    
    def upload_file(self, local_file: str, remote_file: str) -> bool:
        """파일을 업로드합니다."""
        if not self.ftp:
            logger.error("FTP 연결이 없습니다.")
            return False
        
        try:
            with open(local_file, 'rb') as file:
                self.ftp.storbinary(f'STOR {remote_file}', file)
            
            logger.info(f"파일 업로드 완료: {local_file} -> {remote_file}")
            return True
            
        except Exception as e:
            logger.error(f"파일 업로드 실패: {local_file}, 오류: {e}")
            return False
    
    def upload_directory(self, local_dir: str, remote_dir: str = "") -> bool:
        """디렉토리의 모든 파일을 업로드합니다."""
        if not self.ftp:
            logger.error("FTP 연결이 없습니다.")
            return False
        
        try:
            # 원격 디렉토리로 이동 (존재하지 않으면 생성)
            if remote_dir:
                try:
                    self.ftp.cwd(remote_dir)
                except ftplib.error_perm:
                    # 디렉토리가 없으면 생성 시도
                    self._create_remote_directory(remote_dir)
                    self.ftp.cwd(remote_dir)
            
            # 로컬 디렉토리의 모든 파일 업로드
            success_count = 0
            total_count = 0
            
            for filename in os.listdir(local_dir):
                file_path = os.path.join(local_dir, filename)
                if os.path.isfile(file_path):
                    total_count += 1
                    if self.upload_file(file_path, filename):
                        success_count += 1
            
            logger.info(f"디렉토리 업로드 완료: {local_dir} -> {remote_dir} ({success_count}/{total_count})")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"디렉토리 업로드 실패: {local_dir}, 오류: {e}")
            return False
    
    def _create_remote_directory(self, remote_dir: str):
        """원격 디렉토리를 생성합니다."""
        try:
            # 디렉토리 경로를 '/'로 분할
            dirs = remote_dir.split('/')
            current_path = ""
            
            for dir_name in dirs:
                if dir_name:
                    current_path += f"/{dir_name}" if current_path else dir_name
                    try:
                        self.ftp.cwd(current_path)
                    except ftplib.error_perm:
                        # 디렉토리가 없으면 생성
                        self.ftp.mkd(current_path)
                        self.ftp.cwd(current_path)
                        
        except Exception as e:
            logger.error(f"원격 디렉토리 생성 실패: {remote_dir}, 오류: {e}")
            raise
    
    def list_files(self, remote_dir: str = "") -> List[str]:
        """원격 디렉토리의 파일 목록을 가져옵니다."""
        if not self.ftp:
            logger.error("FTP 연결이 없습니다.")
            return []
        
        try:
            if remote_dir:
                self.ftp.cwd(remote_dir)
            
            files = self.ftp.nlst()
            logger.debug(f"원격 디렉토리 파일 목록: {remote_dir}, 파일 수: {len(files)}")
            return files
            
        except Exception as e:
            logger.error(f"파일 목록 조회 실패: {remote_dir}, 오류: {e}")
            return []
    
    def file_exists(self, remote_file: str) -> bool:
        """원격 파일의 존재 여부를 확인합니다."""
        if not self.ftp:
            return False
        
        try:
            self.ftp.size(remote_file)
            return True
        except ftplib.error_perm:
            return False
        except Exception as e:
            logger.error(f"파일 존재 확인 실패: {remote_file}, 오류: {e}")
            return False

def create_ftp_client(ftp_info: Dict) -> Optional[FTPClient]:
    """FTP 정보로부터 FTP 클라이언트를 생성합니다."""
    try:
        host = ftp_info.get('host')
        username = ftp_info.get('username')
        password = ftp_info.get('password')
        port = ftp_info.get('port', 21)
        
        if not all([host, username, password]):
            logger.error("FTP 연결 정보가 불완전합니다.")
            return None
        
        return FTPClient(host, username, password, port)
        
    except Exception as e:
        logger.error(f"FTP 클라이언트 생성 실패: {e}")
        return None

def download_file_with_info(ftp_info: Dict, remote_file: str, local_file: str) -> bool:
    """FTP 정보를 사용하여 파일을 다운로드합니다."""
    ftp_client = create_ftp_client(ftp_info)
    if not ftp_client:
        return False
    
    try:
        if ftp_client.connect():
            return ftp_client.download_file(remote_file, local_file)
        return False
    finally:
        ftp_client.disconnect()

def upload_file_with_info(ftp_info: Dict, local_file: str, remote_file: str) -> bool:
    """FTP 정보를 사용하여 파일을 업로드합니다."""
    ftp_client = create_ftp_client(ftp_info)
    if not ftp_client:
        return False
    
    try:
        if ftp_client.connect():
            return ftp_client.upload_file(local_file, remote_file)
        return False
    finally:
        ftp_client.disconnect()

def upload_directory_with_info(ftp_info: Dict, local_dir: str, remote_dir: str = "") -> bool:
    """FTP 정보를 사용하여 디렉토리를 업로드합니다."""
    ftp_client = create_ftp_client(ftp_info)
    if not ftp_client:
        return False
    
    try:
        if ftp_client.connect():
            return ftp_client.upload_directory(local_dir, remote_dir)
        return False
    finally:
        ftp_client.disconnect()

def batch_upload_files(ftp_info: Dict, file_pairs: List[Tuple[str, str]]) -> Dict[str, bool]:
    """여러 파일을 일괄 업로드합니다."""
    ftp_client = create_ftp_client(ftp_info)
    if not ftp_client:
        return {local_file: False for local_file, _ in file_pairs}
    
    results = {}
    try:
        if ftp_client.connect():
            for local_file, remote_file in file_pairs:
                results[local_file] = ftp_client.upload_file(local_file, remote_file)
        else:
            results = {local_file: False for local_file, _ in file_pairs}
    finally:
        ftp_client.disconnect()
    
    return results

def batch_download_files(ftp_info: Dict, file_pairs: List[Tuple[str, str]]) -> Dict[str, bool]:
    """여러 파일을 일괄 다운로드합니다."""
    ftp_client = create_ftp_client(ftp_info)
    if not ftp_client:
        return {remote_file: False for _, remote_file in file_pairs}
    
    results = {}
    try:
        if ftp_client.connect():
            for remote_file, local_file in file_pairs:
                results[remote_file] = ftp_client.download_file(remote_file, local_file)
        else:
            results = {remote_file: False for _, remote_file in file_pairs}
    finally:
        ftp_client.disconnect()
    
    return results 