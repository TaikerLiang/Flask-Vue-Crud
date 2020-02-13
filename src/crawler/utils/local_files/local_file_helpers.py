from pathlib import Path

LOCAL_PING_HTML = 'ping.html'


def build_local_file_uri(local_file: str) -> str:
    local_folder_path = Path(__file__, is_file=True).parent
    local_file_path = local_folder_path / local_file
    return local_file_path.as_uri()
