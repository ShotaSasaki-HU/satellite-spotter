# app/models/__init__.py
# __init__.py に例えば from .municipality import Municipality と書くことで，app/models/municipality.pyファイルの中に定義されているMunicipalityクラスを，modelsパッケージの直下にあるかのように昇格させることができます．
# このおかげでcrudなどにおいて，from app import models と書けば models.Municipality とテーブル定義を指定できる．
# これが無いと，from app.models.municipality import Municipality と書かなければならない．
from .municipality import Municipality
