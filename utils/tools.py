"""
커스텀 도구 모음
"""

from langchain_core.tools import tool
from database import db_manager


@tool
def search_table_metadata(keywords: str) -> str:
    """
    키워드로 적절한 데이터베이스 테이블 검색

    질문에 포함된 키워드(인구, 세대, 연령 등)로
    어떤 테이블을 사용해야 하는지 찾습니다.

    Args:
        keywords: 검색할 키워드 (예: '인구', '세대', '연령')

    Returns:
        관련 테이블 정보 (테이블명, 설명, 컬럼 정보, 주의사항)
    """
    db = db_manager.get_db()

    # 키워드로 메타데이터 검색
    query = f"""
    SELECT 
        table_name,
        description,
        keywords,
        column_info,
        notes
    FROM table_metadata
    WHERE keywords LIKE '%{keywords}%'
    """

    try:
        result = db.run(query)

        if not result or result == "[]":
            return f"'{keywords}' 키워드와 관련된 테이블을 찾을 수 없습니다."

        return f"검색 결과:\n{result}"

    except Exception as e:
        return f"메타데이터 검색 중 오류: {str(e)}"
