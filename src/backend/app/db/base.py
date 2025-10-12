# app/db/base.py
# マイグレーション用にBaseとmodelsを全て読み込む
from app.db.base_class import Base
from app.models.location import Location
