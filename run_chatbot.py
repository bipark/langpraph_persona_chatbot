#!/usr/bin/env python3
"""
친구 AI 챗봇 실행 스크립트
======================

LangGraph를 활용한 모듈화된 챗봇을 실행합니다.
"""

import os
import sys

# 챗봇 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 로그 디렉토리 확인 및 생성
log_dir = os.path.join(current_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

# API 키 확인
try:
    from chatbot_modules.logging_utils import check_api_key
    check_api_key()
    print("OpenAI API 키가 확인되었습니다.")
except ValueError as e:
    print(f"오류: {e}")
    print("\n.env 파일에 다음과 같이 API 키를 설정하세요:")
    print("OPENAI_API_KEY=your_actual_api_key_here")
    print("또는 환경 변수로 설정하세요.")
    sys.exit(1)
except ImportError:
    print("모듈 import 오류: 필요한 패키지가 설치되어 있는지 확인하세요.")
    print("pip install langchain-core langchain-openai langgraph python-dotenv")
    sys.exit(1)

# 챗봇 실행
from chatbot_modules.main import run_chatbot

if __name__ == "__main__":
    try:
        run_chatbot()
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc() 