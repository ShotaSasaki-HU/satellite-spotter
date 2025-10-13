# app/models/__init__.py
# __init__.py に例えば from .location import Location と書くことで，app/models/location.pyファイルの中に定義されているLocationクラスを，modelsパッケージの直下にあるかのように昇格させることができます．
# このおかげでcrudなどにおいて，from app import models と書けば models.Location とテーブル定義を指定できる．
# これが無いと，from app.models.location import Location と書かなければならない．
from .location import Location
from .spot import Spot
