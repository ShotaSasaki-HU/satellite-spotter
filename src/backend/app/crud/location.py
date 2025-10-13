# app/crud/location.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app import models

def get_locations_by_name_and(db: Session, name: str, skip: int = 0, limit: int = 100):
    """
    スペース区切りの全ての検索クエリを名前に含むLocationをAND検索する．
    """
    keywords = name.split()
    if not keywords:
        return []
    
    # 各キーワードに対する.contains()条件をリストとして作成
    conditions = [models.Location.name.contains(kw) for kw in keywords]

    # and_() を使って全ての条件を結合し、filterに適用
    query = db.query(models.Location).filter(and_(*conditions))

    return query.offset(skip).limit(limit).all()
