import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- ▼▼▼ ここから修正・追記 ▼▼▼ ---

# 1. backend/ をPythonの検索パスに追加
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 2. .envファイルから環境変数を読み込む
from app.core.config import get_settings
settings = get_settings()
LOCAL_DATABASE_URL = settings.DATABASE_URL

# 3. SQLAlchemyモデルをインポートして，Alembicにテーブルの存在を教える．
from app.db import base # app/db/base.py を活用して管理したいモデルを全てインポート

# --- ▲▲▲ ここまで修正・追記 ▲▲▲ ---

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- ▼▼▼ この一行を追記 ▼▼▼ ---
# .iniファイルではなく、上記で生成したURLをAlembicに設定する
config.set_main_option("sqlalchemy.url", LOCAL_DATABASE_URL)
# --- ▲▲▲ この一行を追記 ▲▲▲ ---

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None
target_metadata = base.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # --- ▼▼▼ ここから追-記 ▼▼▼ ---
    
    # どのテーブルをAlembicの監視対象にするかを決めるフィルター関数
    def include_object(object, name, type_, reflected, compare_to):
        # 'table' タイプの場合、alembic_versionテーブルと自分のモデルで定義したテーブルのみを対象とする
        if type_ == "table":
            return name == 'alembic_version' or name in target_metadata.tables
        else:
            return True
            
    # --- ▲▲▲ ここまで追記 ▲▲▲ ---

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # --- ▼▼▼ この一行を追記 ▼▼▼ ---
            include_object=include_object # 上で定義したフィルター関数を設定
            # --- ▲▲▲ この一行を追記 ▲▲▲ ---
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
