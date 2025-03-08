"""
메인 실행 모듈
- 그래프 설정
- 챗봇 실행
"""

import datetime
from typing import Dict, Any

from langgraph.graph import Graph, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from chatbot_modules.models import FRIEND_PERSONA
from chatbot_modules.logging_utils import get_log_filename, check_api_key
from chatbot_modules.state_management import user_state
from chatbot_modules.log_analysis import load_previous_logs, analyze_previous_logs
from chatbot_modules.graph_nodes import (
    manage_messages,
    extract_user_information,
    track_conversation_context,
    generate_response
)

# State 타입 정의
State = Dict[str, Any]

def create_persona_chatbot() -> Graph:
    """페르소나 챗봇 그래프를 생성합니다."""
    
    # 상태 그래프 생성
    graph = StateGraph(State)
    
    # 노드 추가
    graph.add_node("manage_messages", manage_messages)
    graph.add_node("extract_user_information", extract_user_information)
    graph.add_node("track_conversation_context", track_conversation_context)
    graph.add_node("generate_response", generate_response)
    
    # 엣지 추가
    graph.add_edge("manage_messages", "extract_user_information")
    graph.add_edge("extract_user_information", "track_conversation_context")
    graph.add_edge("track_conversation_context", "generate_response")
    
    # 시작 및 종료 노드 설정
    graph.set_entry_point("manage_messages")
    graph.set_finish_point("generate_response")
    
    # LangGraph의 short-term memory 설정
    memory = MemorySaver()
    
    # 체크포인터 설정
    return graph.compile(checkpointer=memory)

def run_chatbot():
    """챗봇을 실행합니다."""
    
    # API 키 확인
    check_api_key()
    
    # 그래프 생성
    chatbot = create_persona_chatbot()
    
    # 초기 상태 설정 및 사용자 ID 생성
    user_id = f"user_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    thread_id = f"thread_{user_id}"
    state = {"messages": [], "user_id": user_id}
    
    print("친구 AI 챗봇이 시작되었습니다.")
    print(f"LLM 통신 로그가 '{get_log_filename()}'에 저장됩니다.")
    print("이전 대화 기록을 로딩하고 분석 중입니다...")
    
    # 이전 로그 로드 및 분석
    previous_logs = load_previous_logs(user_id)
    if previous_logs:
        analysis_result = analyze_previous_logs(previous_logs)
        
        # 사용자 정보 초기화
        if 'user_information' in analysis_result:
            user_info = analysis_result['user_information']
            user_state.update_user_information(user_id, user_info)
            print(f"사용자 정보 {len(user_info.keys())}개 항목 로드 완료")
            
        # 대화 맥락 초기화
        if 'conversation_context' in analysis_result:
            context = analysis_result['conversation_context']
            user_state.update_conversation_context(user_id, context)
            
            # 대화 맥락 정보 출력
            if context.get('current_context'):
                print("이전 대화 맥락 로드 완료")
                
            if context.get('main_topics'):
                print(f"주요 주제 {len(context['main_topics'])}개 로드 완료")
                
        print("이전 대화 기록 분석이 완료되었습니다.")
    else:
        print("이전 대화 기록이 없습니다.")
    
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.")
    print("-" * 50)
    
    # 초기 인사말
    print(f"{FRIEND_PERSONA['name']}: {FRIEND_PERSONA['greeting']}")
    
    while True:
        # 사용자 입력 받기
        user_input = input("\n사용자: ")
        
        # 종료 명령 확인
        if user_input.lower() in ["exit", "quit", "종료"]:
            print(f"\n{FRIEND_PERSONA['name']}: 대화를 종료합니다. 다음에 또 만나요!")
            break
        
        # 사용자 메시지 추가
        state["messages"].append({"role": "user", "content": user_input})
        
        # 챗봇 실행
        result = chatbot.invoke(state, {"configurable": {"thread_id": thread_id}})
        
        # 응답 출력
        if "response" in result:
            print(f"\n{FRIEND_PERSONA['name']}: {result['response']}")
        else:
            print(f"\n{FRIEND_PERSONA['name']}: 죄송합니다. 응답을 생성하는 데 문제가 발생했습니다.")
        
        # 상태 업데이트
        state = result

if __name__ == "__main__":
    # 챗봇 실행
    run_chatbot() 