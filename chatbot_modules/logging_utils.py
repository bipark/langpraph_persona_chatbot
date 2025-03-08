"""
로깅 관련 유틸리티 모듈
- 로그 디렉토리 생성
- 로거 설정
- LLM 통신 로깅 기능
- API 키 설정 관리
"""

import os
import json
import logging
import datetime
from uuid import uuid4
from typing import Any, Dict
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 확인
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 로그 디렉토리 설정
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 현재 시간을 기반으로 로그 파일 이름 생성
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOG_DIR, f"llm_log_{current_time}.json")

# 로그 설정
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# httpx 로거의 레벨을 WARNING으로 설정하여 INFO 로그를 숨김
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger("llm_communication")

# 콘솔 핸들러를 모두 제거
for handler in logger.handlers:
    logger.removeHandler(handler)

# 파일 핸들러 추가
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')  # 간단한 형식 (JSON만 저장)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.propagate = False  # 상위 로거로 전파하지 않음

def check_api_key():
    """API 키가 설정되어 있는지 확인합니다."""
    if not OPENAI_API_KEY:
        raise ValueError(
            "OpenAI API 키가 설정되지 않았습니다. "
            "환경 변수 OPENAI_API_KEY를 설정하거나 .env 파일에 OPENAI_API_KEY=your_key 형식으로 추가하세요."
        )
    return True

def log_llm_communication(request_data: Any, response_data: Any, source: str) -> None:
    """LLM 통신 내용을 로깅합니다.
    
    Args:
        request_data: LLM에 전송된 요청 데이터
        response_data: LLM에서 받은 응답 데이터
        source: 로그 소스 (예: 'ChatOpenAI')
    """
    try:
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "id": str(uuid4()),
            "source": source,
            "request": request_data,
            "response": response_data
        }
        
        # JSON 직렬화 시도
        try:
            log_json = json.dumps(log_entry, ensure_ascii=False)
            logger.info(log_json)
            # print(f"LLM 통신 로그가 '{log_filename}'에 저장되었습니다.")
        except TypeError as e:
            # 직렬화 할 수 없는 객체가 있는 경우, 간단한 형태로 로깅
            simplified_log = {
                "timestamp": datetime.datetime.now().isoformat(),
                "id": str(uuid4()),
                "source": source,
                "error": f"로깅 중 직렬화 오류 발생: {e}"
            }
            logger.info(json.dumps(simplified_log, ensure_ascii=False))
            # print(f"로깅 중 직렬화 오류 발생, 간소화된 로그가 저장되었습니다.")
    except Exception as e:
        print(f"로깅 시스템 오류: {e}")

def get_log_filename() -> str:
    """현재 로그 파일 이름을 반환합니다."""
    return log_filename 