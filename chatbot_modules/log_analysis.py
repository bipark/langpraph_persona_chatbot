"""
로그 분석 모듈
- 로그 파일 로딩
- 로그 데이터 분석
- 대화 요약
"""

import os
import json
import datetime
import traceback
from typing import List, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

from chatbot_modules.logging_utils import LOG_DIR
from chatbot_modules.llm_wrappers import LoggingChatOpenAI

def load_previous_logs(user_id: str) -> List[Dict]:
    """이전 로그 파일들을 로드하고 해당 사용자의 대화 내용을 반환합니다."""
    all_logs = []
    
    try:
        # logs 디렉토리의 모든 로그 파일 검색
        log_files = [f for f in os.listdir(LOG_DIR) if f.endswith('.json')]
        
        for log_file in log_files:
            file_path = os.path.join(LOG_DIR, log_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            # 공백 및 빈 줄 스킵
                            if not line.strip():
                                continue
                                
                            log_entry = json.loads(line.strip())
                            
                            # 유효한 로그 항목만 처리 (필수 필드 확인)
                            if 'request' in log_entry and 'response' in log_entry:
                                # 타임스탬프가 없는 경우 추가
                                if 'timestamp' not in log_entry:
                                    log_entry['timestamp'] = datetime.datetime.now().isoformat()
                                    
                                # 소스 정보가 없는 경우 추가
                                if 'source' not in log_entry:
                                    log_entry['source'] = 'unknown'
                                    
                                all_logs.append(log_entry)
                        except json.JSONDecodeError:
                            print(f"잘못된 JSON 형식의 로그 라인 무시: {file_path}")
                            continue
                        except Exception as e:
                            print(f"로그 라인 처리 중 오류 발생: {e}")
                            continue
            except Exception as e:
                print(f"로그 파일 '{file_path}' 열기 실패: {e}")
                continue
        
        # 로그를 타임스탬프 기준으로 정렬 (가장 오래된 것부터)
        all_logs.sort(key=lambda x: x.get('timestamp', ''))
        
        valid_log_count = len(all_logs)
        print(f"로그 파일 로딩 완료: {valid_log_count}개의 유효한 대화 로그 항목 로딩")
                        
    except Exception as e:
        print(f"로그 로딩 중 오류 발생: {e}")
        traceback.print_exc()
        
    return all_logs

def summarize_previous_conversations(logs: List[Dict]) -> str:
    """이전 대화에서 중요한 내용을 요약하여 반환합니다."""
    try:
        # ChatOpenAI 인스턴스 생성
        llm = LoggingChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
        
        # 로그에서 대화 내용 추출
        conversations = []
        for log in logs:
            # 요청 처리
            if 'request' in log:
                request = log['request']
                # 요청이 딕셔너리인 경우
                if isinstance(request, dict) and 'messages' in request:
                    messages = request['messages']
                    if isinstance(messages, list):
                        user_messages = [msg for msg in messages if isinstance(msg, dict) 
                                        and 'role' in msg and msg['role'] == 'user' 
                                        and 'content' in msg]
                        if user_messages:
                            latest_user_msg = user_messages[-1]
                            conversations.append(f"사용자: {latest_user_msg['content']}")
                # 요청이 문자열인 경우
                elif isinstance(request, str):
                    conversations.append(f"사용자: {request}")
                # 요청이 리스트인 경우
                elif isinstance(request, list):
                    for item in request:
                        if isinstance(item, dict) and 'role' in item and item['role'] == 'user' and 'content' in item:
                            conversations.append(f"사용자: {item['content']}")
            
            # 응답 처리
            if 'response' in log:
                response = log['response']
                # 응답이 딕셔너리인 경우
                if isinstance(response, dict):
                    if 'content' in response:
                        conversations.append(f"챗봇: {response['content']}")
                    elif 'choices' in response and isinstance(response['choices'], list) and len(response['choices']) > 0:
                        # OpenAI API 직접 응답 형식
                        choice = response['choices'][0]
                        if isinstance(choice, dict) and 'message' in choice:
                            message = choice['message']
                            if isinstance(message, dict) and 'content' in message:
                                conversations.append(f"챗봇: {message['content']}")
                # 응답이 문자열인 경우
                elif isinstance(response, str):
                    conversations.append(f"챗봇: {response}")
        
        # 최근 50개의 대화만 사용
        recent_conversations = conversations[-50:]
        conversation_text = "\n".join(recent_conversations)
        
        if not conversation_text:
            return ""
            
        # 요약 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
            다음은 이전 대화 기록입니다. 이 대화의 주요 내용을 200자 이내로 간결하게 요약해주세요.
            중요한 정보, 주제 및 맥락만 포함하세요.
            """),
            HumanMessage(content=f"대화 기록:\n\n{conversation_text}")
        ])
        
        # 요약 실행
        chain = prompt | llm | StrOutputParser()
        summary = chain.invoke({})
        
        return summary
        
    except Exception as e:
        print(f"대화 요약 중 오류 발생: {e}")
        traceback.print_exc()
        return ""

def analyze_previous_logs(logs: List[Dict]) -> Dict[str, Any]:
    """이전 로그를 분석하여 사용자 정보와 대화 맥락을 추출합니다."""
    try:
        # ChatOpenAI 인스턴스 생성
        llm = LoggingChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
        
        # 로그에서 대화 내용 추출
        conversations = []
        for log in logs:
            # 요청 데이터 처리
            if 'request' in log:
                request = log['request']
                # request가 딕셔너리인 경우
                if isinstance(request, dict) and 'messages' in request:
                    messages = request['messages']
                    if isinstance(messages, list):
                        for msg in messages:
                            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                                if msg['role'] in ['user', 'assistant']:
                                    conversations.append(f"{msg['role']}: {msg['content']}")
                # request가 문자열인 경우 (직접 내용으로 처리)
                elif isinstance(request, str):
                    conversations.append(f"request: {request}")
                # request가 리스트인 경우 (각 항목 처리)
                elif isinstance(request, list):
                    for item in request:
                        if isinstance(item, dict) and 'role' in item and 'content' in item:
                            conversations.append(f"{item['role']}: {item['content']}")
            
            # 응답 데이터 처리
            if 'response' in log:
                response = log['response']
                # response가 딕셔너리인 경우
                if isinstance(response, dict):
                    if 'content' in response:
                        conversations.append(f"assistant: {response['content']}")
                    elif 'choices' in response and isinstance(response['choices'], list) and len(response['choices']) > 0:
                        # OpenAI API 직접 응답 형식
                        choice = response['choices'][0]
                        if isinstance(choice, dict) and 'message' in choice:
                            message = choice['message']
                            if isinstance(message, dict) and 'content' in message:
                                conversations.append(f"assistant: {message['content']}")
                # response가 문자열인 경우 (직접 내용으로 처리)
                elif isinstance(response, str):
                    conversations.append(f"assistant: {response}")
        
        # 최근 100개의 대화만 사용
        recent_conversations = conversations[-100:]
        conversation_text = "\n".join(recent_conversations)
        
        if not conversation_text:
            return {}
        
        # 분석 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
            다음 대화 기록을 분석하여 중요한 정보를 추출하세요. JSON 형식으로 다음 정보를 반환하세요:
            
            1. user_information: {
                "name": str | null,
                "age": int | null,
                "occupation": str | null,
                "location": str | null,
                "interests": string[],
                "preferences": {key: value},
                "goals": string[],
                "family": {key: value},
                "contact_info": str | null
            }
            
            2. conversation_context: {
                "main_topics": string[],
                "current_context": str,
                "pending_questions": string[],
                "references": {key: value}
            }
            
            대화에서 명확하게 언급된 정보만 포함하세요. 추측하지 마세요.
            """),
            HumanMessage(content=f"다음 대화 기록을 분석하세요:\n\n{conversation_text}")
        ])
        
        # 분석 실행
        chain = (
            prompt 
            | llm 
            | StrOutputParser() 
            | (lambda x: json.loads(x) if x.strip() else {})
        )
        
        result = chain.invoke({})
        
        # 대화 요약 추가
        if result and 'conversation_context' in result:
            conversation_summary = summarize_previous_conversations(logs)
            if conversation_summary:
                if 'current_context' in result['conversation_context']:
                    if result['conversation_context']['current_context']:
                        result['conversation_context']['current_context'] += f"\n\n이전 대화 요약: {conversation_summary}"
                    else:
                        result['conversation_context']['current_context'] = f"이전 대화 요약: {conversation_summary}"
        
        return result
        
    except Exception as e:
        print(f"로그 분석 중 오류 발생: {e}")
        traceback.print_exc()
        return {} 