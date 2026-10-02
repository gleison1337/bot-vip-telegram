import aiosqlite
from datetime import datetime, timedelta

DB_NAME = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS assinaturas (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                data_inicio TEXT,
                data_fim TEXT,
                status TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cobrancas (
                correlation_id TEXT PRIMARY KEY,
                charge_id TEXT,
                user_id INTEGER,
                plano_key TEXT,
                status TEXT
            )
        """)
        await db.commit()

async def salvar_cobranca(correlation_id: str, charge_id: str, user_id: int, plano_key: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO cobrancas (correlation_id, charge_id, user_id, plano_key, status) VALUES (?, ?, ?, ?, 'PENDING')",
            (correlation_id, charge_id, user_id, plano_key)
        )
        await db.commit()

async def get_cobranca_por_correlation(correlation_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id, plano_key FROM cobrancas WHERE correlation_id = ?",
            (correlation_id,)
        ) as cursor:
            return await cursor.fetchone()

async def atualizar_status_cobranca(correlation_id: str, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE cobrancas SET status = ? WHERE correlation_id = ?",
            (status, correlation_id)
        )
        await db.commit()

async def ativar_ou_renovar_assinatura(user_id: int, username: str, dias: int):
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=dias)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO assinaturas (user_id, username, data_inicio, data_fim, status)
            VALUES (?, ?, ?, ?, 'ativo')
            ON CONFLICT(user_id) DO UPDATE SET
                data_fim = datetime(data_fim, '+' || ? || ' days'),
                status = 'ativo'
        """, (user_id, username, data_inicio.isoformat(), data_fim.isoformat(), dias))
        await db.commit()

async def get_assinaturas_expiradas():
    agora = datetime.now().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id FROM assinaturas WHERE status = 'ativo' AND data_fim <= ?",
            (agora,)
        ) as cursor:
            return await cursor.fetchall()

async def desativar_assinatura(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE assinaturas SET status = 'expirado' WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()