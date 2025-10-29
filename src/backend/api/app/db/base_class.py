# app/db/base_class.py
# Baseは，全てのモデルが共通で継承する基底クラスなので，アプリ全体で1か所に定義して，それを各モデルでimportして使う．
from sqlalchemy.orm import declarative_base

Base = declarative_base()
