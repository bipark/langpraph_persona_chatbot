"""
LangGraph 노드 함수 모듈
- manage_messages: 메시지 관리 노드
- track_conversation_context: 대화 맥락 추적 노드
- extract_user_information: 사용자 정보 추출 노드
- generate_response: 응답 생성 노드
"""

import json
import datetime
import traceback
from typing import Dict, Any, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

from chatbot_modules.models import FRIEND_PERSONA
from chatbot_modules.state_management import user_state
from chatbot_modules.llm_wrappers import LoggingChatOpenAI
from chatbot_modules.utils import _contains_personal_info, enhance_system_prompt

# State 타입 정의
State = Dict[str, Any]

def manage_messages(state: State) -> State:
    """사용자와 에이전트 간의 메시지를 관리하고 처리합니다."""
    user_id = state["user_id"]
    messages = state["messages"]
    
    # 대화 기록 저장
    user_state.save_conversation(user_id, messages)
    
    # FRIEND_PERSONA의 시스템 프롬프트 강화
    enhanced_system_prompt = enhance_system_prompt(user_id, FRIEND_PERSONA["system_prompt"])
    
    # 향상된 시스템 프롬프트로 메시지 업데이트
    system_message = SystemMessage(content=enhanced_system_prompt)
    
    # 사용자 및 어시스턴트 메시지 변환
    chat_messages = []
    for msg in messages:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            if msg["role"] == "user":
                chat_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_messages.append(AIMessage(content=msg["content"]))
        else:
            # 이미 LangChain 메시지 객체인 경우
            chat_messages.append(msg)
    
    # 업데이트된 메시지로 상태 업데이트
    state["updated_messages"] = [system_message] + chat_messages
    
    return state

def track_conversation_context(state: State) -> State:
    """대화 맥락을 추적하고 업데이트합니다."""
    try:
        user_id = state["user_id"]
        messages = state.get("updated_messages", state.get("messages", []))
        
        # 메시지가 없으면 아무 작업도 하지 않음
        if not messages:
            return state
            
        # 마지막 메시지를 가져옴 (여러 형식 지원)
        last_message = None
        for msg in reversed(messages):
            if isinstance(msg, dict) and "role" in msg and msg["role"] == "user":
                last_message = msg["content"]
                break
            elif isinstance(msg, HumanMessage):
                last_message = msg.content
                break
                
        if not last_message:
            return state
            
        # 현재 대화 맥락 가져오기
        context = user_state.get_conversation_context(user_id)
        
        # ChatOpenAI 인스턴스 생성
        llm = LoggingChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
        
        # 대화 맥락 분석
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""
            다음 대화에서 사용자의 마지막 메시지를 분석하여 대화 맥락 정보를 JSON 형식으로 반환하세요:
            
            1. main_topics: 주요 주제들의 배열(최대 3개, 짧은 키워드로)
            2. current_context: 현재 맥락에 대한 간단한 요약 (최대 100자)
            3. pending_questions: 아직 대답하지 않은 사용자의 질문들 배열
            4. references: 대화 중 언급된 참조 정보 객체 (키-값 쌍)
            
            이전 맥락 정보:
            {json.dumps(context, ensure_ascii=False, indent=2)}
            
            새로운 정보만 추가하고, 기존 맥락과 일관성 있게 업데이트하세요.
            """),
            HumanMessage(content=f"사용자의 마지막 메시지: {last_message}")
        ])
        
        # 분석 실행
        chain = (
            prompt 
            | llm 
            | StrOutputParser() 
            | (lambda x: json.loads(x) if x.strip() else {})
        )
        
        analysis_result = chain.invoke({})
        
        # 맥락 업데이트
        if analysis_result:
            context_updates = {}
            
            # 주요 주제 업데이트
            if 'main_topics' in analysis_result and analysis_result['main_topics']:
                # 기존 주제와 새 주제 합쳐서 중복 제거 후 최대 5개로 제한
                existing_topics = context.get('main_topics', [])
                new_topics = analysis_result['main_topics']
                all_topics = list(dict.fromkeys(existing_topics + new_topics))
                context_updates['main_topics'] = all_topics[:5]
                
            # 현재 맥락 업데이트
            if 'current_context' in analysis_result and analysis_result['current_context']:
                context_updates['current_context'] = analysis_result['current_context']
                
            # 대답하지 않은 질문 업데이트
            if 'pending_questions' in analysis_result and analysis_result['pending_questions']:
                existing_questions = context.get('pending_questions', [])
                new_questions = analysis_result['pending_questions']
                all_questions = list(dict.fromkeys(existing_questions + new_questions))
                context_updates['pending_questions'] = all_questions
                
            # 참조 정보 업데이트
            if 'references' in analysis_result and analysis_result['references']:
                existing_refs = context.get('references', {})
                existing_refs.update(analysis_result['references'])
                context_updates['references'] = existing_refs
                
            # 마지막 업데이트 시간
            current_time = datetime.datetime.now().isoformat()
            context_updates['last_update_time'] = current_time
            
            # 맥락 업데이트
            if context_updates:
                user_state.update_conversation_context(user_id, context_updates)
        
    except Exception as e:
        print(f"대화 맥락 업데이트 중 오류 발생: {e}")
        traceback.print_exc()
        
    return state

def extract_user_information(state: State) -> State:
    """대화에서 사용자 정보를 추출합니다."""
    try:
        user_id = state["user_id"]
        messages = state.get("updated_messages", state.get("messages", []))
        
        # 5턴 마다 사용자 정보 업데이트 (주기적 업데이트)
        conversation_count = len([msg for msg in messages 
                                 if (isinstance(msg, dict) and msg.get("role") == "user") or 
                                    isinstance(msg, HumanMessage)])
        
        # 대화가 최소 3턴 이상이고, 3턴 마다 또는 마지막 메시지에 개인정보가 있을 가능성이 높을 때 분석
        if conversation_count >= 3 and (conversation_count % 3 == 0 or _contains_personal_info(messages)):
            # 최근 대화만 사용
            recent_messages = messages[-10:]
            
            # 메시지 텍스트 추출
            conversation_text = ""
            for msg in recent_messages:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    role = "사용자" if msg["role"] == "user" else "챗봇"
                    conversation_text += f"{role}: {msg['content']}\n"
                elif isinstance(msg, (HumanMessage, AIMessage)):
                    role = "사용자" if isinstance(msg, HumanMessage) else "챗봇"
                    conversation_text += f"{role}: {msg.content}\n"
                
            # ChatOpenAI 인스턴스 생성
            llm = LoggingChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
            
            # 현재 사용자 정보 가져오기
            current_info = user_state.get_user_information(user_id)
            
            # 프롬프트 생성
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""
                다음 대화에서 사용자에 대한 개인 정보를 추출하세요.
                이미 알고 있는 정보: {json.dumps(current_info, ensure_ascii=False, indent=2)}
                
                새로운 정보만 추출하고, 확실한 정보만 포함하세요. 추측하지 마세요.
                결과를 다음 JSON 형식으로 반환하세요:
                {{
                  "name": null,
                  "age": null,
                  "occupation": null,
                  "location": null, 
                  "interests": [],
                  "preferences": {{}},
                  "goals": [],
                  "family": {{}},
                  "contact_info": null
                }}
                """),
                HumanMessage(content=f"대화:\n{conversation_text}")
            ])
            
            # 실행
            chain = (
                prompt 
                | llm 
                | StrOutputParser()
                | (lambda x: json.loads(x) if x.strip() else {})
            )
            
            # 추출 실행
            try:
                result = chain.invoke({})
                
                # 비어있지 않은 결과가 있을 때만 업데이트
                if result:
                    user_state.update_user_information(user_id, result)
            except Exception as e:
                print(f"사용자 정보 추출 중 파싱 오류: {e}")
    
    except Exception as e:
        print(f"사용자 정보 추출 중 오류 발생: {e}")
        traceback.print_exc()
        
    return state

def generate_response(state: State) -> State:
    """새로운 응답을 생성합니다."""
    user_id = state["user_id"]
    
    try:
        # LLM 인스턴스 생성
        llm = LoggingChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
        
        # 응답 생성
        response = llm.invoke(state["updated_messages"])
        
        # 응답 내용을 상태에 추가
        response_content = response.content
        
        # 메시지 목록에 응답 추가
        state["messages"].append({"role": "assistant", "content": response_content})
        
        # 응답 결과를 별도 키에 저장 (출력용)
        state["response"] = response_content
        
    except Exception as e:
        print(f"응답 생성 중 오류 발생: {e}")
        state["response"] = "죄송합니다. 응답을 생성하는 데 문제가 발생했습니다."
    
    return state 