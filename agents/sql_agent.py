"""
SQL Agent 생성 및 관리 모듈
"""

from langchain_upstage import ChatUpstage
from langchain_community.agent_toolkits import create_sql_agent
from config import settings
from database import db_manager
from utils import search_table_metadata


class SQLAgentManager:
    """SQL Agent 관리 클래스"""

    def __init__(self):
        self.llm = None
        self.agent = None
        self.db = None

    def initialize(self):
        """Agent 초기화"""
        # LLM 초기화
        self.llm = ChatUpstage(
            api_key=settings.UPSTAGE_API_KEY,
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
        )
        print(f"LLM 초기화 완료: {settings.MODEL_NAME}")

        # DB 연결
        self.db = db_manager.get_db()

        # System Prompt 정의
        system_prefix = """
당신은 대한민국 통계청 데이터 분석 전문가입니다.
통계청에서 제공하는 주민등록 인구, 경제활동, 가구 등 
각종 통계 데이터를 정확하게 조회하고 해석합니다.

**현재 데이터베이스:**
주민등록 인구통계 (2016년 1월 ~ 2025년 10월)
- 행정구역별 성별/연령대별 인구수
- 세대수(가구수) 통계

**질문 분석 절차:**
1. 먼저 search_table_metadata 도구를 사용하여 적절한 테이블을 찾으세요
2. search_table_metadata 사용 시 핵심 키워드 1개만 전달하세요
   - 올바른 예시: search_table_metadata('인구')
   - 올바른 예시: search_table_metadata('세대')
   - 잘못된 예시: search_table_metadata('총인구수, 인구수, 서울특별시')
3. 검색 결과가 없으면 다른 키워드로 재시도하세요
4. 메타데이터의 note(주의사항)를 반드시 확인하세요

**테이블 선택 가이드:**
- "총인구수", "인구수", "사람", "남자", "여자", "성별" → population_gender_stats
- "세대수", "가구수", "household" → population_stats
- "연령대", "나이", "고령", "청년", "노인" → population_age_stats

**SQL 작성 규칙:**
1. SQLite 문법만 사용하세요
2. SELECT 쿼리만 작성하세요 (INSERT, UPDATE, DELETE 금지)
3. 테이블명과 컬럼명을 스키마에 있는 그대로 정확히 사용하세요
4. 한국 행정구역명은 전체 이름 사용 (예: '서울특별시', '경기도')
5. 쿼리는 반드시 세미콜론(;)으로 끝내세요
6. 날짜 형식은 'YYYY-MM' 형식입니다 (예: '2024-10')
7. NULL 값 제외: WHERE 절에 "년월" IS NOT NULL AND "값" IS NOT NULL 추가

**주의사항:**
- 데이터가 없으면 "해당 조건의 데이터가 없습니다"라고 명확히 알려주세요
- 추측하지 말고 실제 데이터만 기반으로 답변하세요
"""
        system_suffix = """
**최종 답변 작성 규칙:**
1. 모든 답변은 반드시 한국어로 작성하세요
2. 수치는 쉼표로 구분하세요 (예: 9,422,094명)
3. 2-3문장으로 간결하고 명확하게 답변하세요
4. 조회 기준 시점(년월)을 명시하세요
5. 데이터 출처 테이블을 언급하세요

절대 영어로 답변하지 마세요.
반드시 한국어로만 답변하세요.
"""

        # SQL Agent 생성 (커스텀 도구 포함)
        self.agent = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="openai-tools",
            verbose=True,
            handle_parsing_errors=True,
            extra_tools=[search_table_metadata],
            prefix=system_prefix + "\n\n" + system_suffix,
            # suffix=system_suffix,
        )
        print("SQL Agent 생성 완료 (메타데이터 검색 도구 포함)")

        return self.agent

    def query(self, question: str) -> dict:
        """
        자연어 질문을 SQL로 변환하여 실행

        Args:
            question: 자연어 질문

        Returns:
            dict: {
                "question": 질문,
                "answer": 답변,
                "success": 성공 여부,
                "error": 에러 메시지 (있을 경우)
            }
        """
        if self.agent is None:
            self.initialize()

        try:
            print(f"\n{'='*60}")
            print(f"질문: {question}")
            print(f"{'='*60}")

            result = self.agent.invoke({"input": question})

            return {
                "question": question,
                "answer": result.get("output", ""),
                "success": True,
                "error": None,
            }

        except Exception as e:
            print(f"에러 발생: {e}")
            return {
                "question": question,
                "answer": None,
                "success": False,
                "error": str(e),
            }

    def get_agent(self):
        """Agent 인스턴스 반환"""
        if self.agent is None:
            self.initialize()
        return self.agent


# 전역 Agent 매니저 인스턴스
sql_agent_manager = SQLAgentManager()
