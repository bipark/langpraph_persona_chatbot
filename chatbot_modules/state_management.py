"""
사용자 상태 관리 모듈
- UserState: 사용자의 대화 기록, 정보, 맥락을 관리하는 클래스
"""

import datetime
from typing import Any, Dict, List

from chatbot_modules.models import ConversationContext, UserInformation
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class UserState:
    """사용자 상태를 관리하는 클래스"""
    
    def __init__(self):
        """초기화"""
        self.conversation_history = {}  # 대화 기록 (user_id: List[Dict])
        self.user_information = {}  # 사용자 정보 (user_id: Dict)
        self.conversation_contexts = {}  # 대화 맥락 (user_id: Dict)

    def save_conversation(self, user_id: str, messages: List[Any]):
        """대화 내용을 저장합니다."""
        
        # 사용자 ID가 존재하지 않으면 초기화
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # 메시지 형식 정규화 및 저장
        normalized_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                normalized_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": datetime.datetime.now().isoformat()
                })
            else:
                # LangChain 메시지 객체 처리
                normalized_messages.append({
                    "role": msg.type if hasattr(msg, 'type') else (
                        "system" if isinstance(msg, SystemMessage) else
                        "user" if isinstance(msg, HumanMessage) else
                        "assistant"
                    ),
                    "content": msg.content,
                    "timestamp": datetime.datetime.now().isoformat()
                })
        
        # 시스템 메시지는 저장하지 않음
        filtered_messages = [msg for msg in normalized_messages if msg["role"] != "system"]
        
        # 대화 내용 업데이트
        self.conversation_history[user_id] = filtered_messages
        
    def update_user_information(self, user_id: str, info: Dict[str, Any]):
        """사용자 정보를 업데이트합니다."""
        if user_id not in self.user_information:
            self.user_information[user_id] = UserInformation().dict()
            
        # 딕셔너리 합치기 (중첩된 딕셔너리와 리스트 처리)
        for key, value in info.items():
            if value is not None and value != "":
                if key in ["interests", "goals"] and isinstance(value, list):
                    # 리스트 항목 추가 (중복 제거)
                    current_list = self.user_information[user_id].get(key, [])
                    self.user_information[user_id][key] = list(set(current_list + value))
                elif key in ["preferences", "family"] and isinstance(value, dict):
                    # 딕셔너리 업데이트
                    current_dict = self.user_information[user_id].get(key, {})
                    current_dict.update(value)
                    self.user_information[user_id][key] = current_dict
                else:
                    # 일반 값 업데이트
                    self.user_information[user_id][key] = value
    
    def get_user_information(self, user_id: str) -> Dict[str, Any]:
        """사용자 정보를 반환합니다."""
        if user_id not in self.user_information:
            return {}
            
        return self.user_information[user_id]
        
    def update_conversation_context(self, user_id: str, context_updates: Dict[str, Any]):
        """대화 맥락을 업데이트합니다."""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = ConversationContext().dict()
            
        # 필드별 업데이트 처리
        for key, value in context_updates.items():
            if key == "main_topics" and isinstance(value, list):
                # 기존 주제와 병합하고 중복 제거
                current_topics = self.conversation_contexts[user_id].get("main_topics", [])
                updated_topics = list(set(current_topics + value))
                # 최대 10개 주제만 유지 (오래된 주제 제거)
                self.conversation_contexts[user_id]["main_topics"] = updated_topics[-10:]
            elif key == "current_context" and value:
                # 현재 맥락 업데이트
                self.conversation_contexts[user_id]["current_context"] = value
            elif key == "pending_questions" and isinstance(value, list):
                # 대기 중인 질문 업데이트
                current_questions = self.conversation_contexts[user_id].get("pending_questions", [])
                # 새 질문 추가
                self.conversation_contexts[user_id]["pending_questions"] = current_questions + value
            elif key == "references" and isinstance(value, dict):
                # 참조 정보 업데이트
                current_refs = self.conversation_contexts[user_id].get("references", {})
                current_refs.update(value)
                self.conversation_contexts[user_id]["references"] = current_refs
                
        # 마지막 업데이트 시간 기록
        self.conversation_contexts[user_id]["last_update_time"] = datetime.datetime.now().isoformat()
    
    def remove_pending_question(self, user_id: str, question: str):
        """답변된 질문을 대기 목록에서 제거합니다."""
        if user_id in self.conversation_contexts and "pending_questions" in self.conversation_contexts[user_id]:
            questions = self.conversation_contexts[user_id]["pending_questions"]
            if question in questions:
                questions.remove(question)
                self.conversation_contexts[user_id]["pending_questions"] = questions
    
    def get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """대화 맥락을 반환합니다."""
        if user_id not in self.conversation_contexts:
            return ConversationContext().dict()
            
        return self.conversation_contexts[user_id]

# 전역 사용자 상태 객체
user_state = UserState() 