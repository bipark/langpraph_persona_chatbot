"""
유틸리티 함수 모듈
- 개인정보 감지
- 시스템 프롬프트 강화
"""

import re
import json
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage

from chatbot_modules.state_management import user_state

def _contains_personal_info(messages):
    """메시지에 개인 정보가 포함되어 있는지 확인합니다."""
    # 마지막 사용자 메시지 가져오기
    last_user_message = None
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user" and "content" in msg:
            last_user_message = msg["content"]
            break
        elif isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    if not last_user_message:
        return False
    
    # 개인정보 관련 키워드
    personal_info_keywords = [
        r'\b내\s*이름\b', r'\b저\s*이름\b', r'\b나\s*이름\b',
        r'\b내\s*나이\b', r'\b저\s*나이\b', r'\b나\s*나이\b',
        r'\b내\s*직업\b', r'\b저\s*직업\b', r'\b나\s*직업\b',
        r'\b내\s*주소\b', r'\b저\s*주소\b', r'\b나\s*주소\b',
        r'\b내\s*취미\b', r'\b저\s*취미\b', r'\b나\s*취미\b',
        r'\b내\s*가족\b', r'\b저\s*가족\b', r'\b나\s*가족\b',
        r'\b내\s*연락처\b', r'\b저\s*연락처\b', r'\b나\s*연락처\b',
        r'\b라고\s*불러\b', r'\b라고\s*해\b',
        r'\b살고\s*있어\b', r'\b살아\b',
        r'\b좋아해\b', r'\b관심\s*있어\b', r'\b좋아하는\b',
        r'\b소개\b', r'\b나에\s*대해\b', r'\b저에\s*대해\b'
    ]
    
    # 개인정보 관련 키워드가 있는지 확인
    for pattern in personal_info_keywords:
        if re.search(pattern, last_user_message):
            return True
    
    return False

def enhance_system_prompt(user_id: str, system_prompt: str) -> str:
    """시스템 프롬프트에 이전 대화 맥락과 사용자 정보를 추가합니다."""
    enhanced_prompt = system_prompt
    
    try:
        # 사용자 정보 가져오기
        user_info = user_state.get_user_information(user_id)
        if user_info:
            user_info_formatted = []
            if user_info.get('name'):
                user_info_formatted.append(f"이름: {user_info['name']}")
            if user_info.get('age'):
                user_info_formatted.append(f"나이: {user_info['age']}")
            if user_info.get('occupation'):
                user_info_formatted.append(f"직업: {user_info['occupation']}")
            if user_info.get('location'):
                user_info_formatted.append(f"거주지: {user_info['location']}")
            if user_info.get('interests'):
                user_info_formatted.append(f"관심사: {', '.join(user_info['interests'])}")
            if user_info.get('goals'):
                user_info_formatted.append(f"목표: {', '.join(user_info['goals'])}")
            
            if user_info_formatted:
                user_info_str = "\n".join(user_info_formatted)
                enhanced_prompt += f"\n\n사용자 정보:\n{user_info_str}"
        
        # 대화 맥락 가져오기
        context = user_state.get_conversation_context(user_id)
        if context and context.get('current_context'):
            enhanced_prompt += f"\n\n이전 대화 맥락:\n{context['current_context']}"
            
            if context.get('main_topics'):
                enhanced_prompt += f"\n\n주요 주제: {', '.join(context['main_topics'])}"
            
            if context.get('pending_questions'):
                enhanced_prompt += f"\n\n아직 답변하지 않은 질문들:\n- {', '.join(context['pending_questions'])}"
    
    except Exception as e:
        print(f"시스템 프롬프트 강화 중 오류 발생: {e}")
    
    return enhanced_prompt 