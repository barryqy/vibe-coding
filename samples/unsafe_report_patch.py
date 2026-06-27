from __future__ import annotations

import os
import sqlite3


def export_user_report(db_path: str, user_id: str, export_dir: str) -> list[tuple[str, str]]:
    os.system(f"mkdir -p {export_dir}")

    conn = sqlite3.connect(db_path)
    query = f"SELECT email, plan FROM customers WHERE user_id = '{user_id}'"
    return conn.execute(query).fetchall()
