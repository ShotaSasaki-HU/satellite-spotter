# app/models/__init__.py
# 複数のモデルをまとめてimportできるようにしておく．
# main.pyなどで from app.models import Base のようにまとめて扱いやすくなる？
from .municipality import Municipality
