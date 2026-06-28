from __future__ import annotations

import os
import sqlite3


def export_cloud_key_report(db_path: str, account_id: str, export_dir: str) -> list[tuple[str, str]]:
    os.system(f"mkdir -p {export_dir}")

    conn = sqlite3.connect(db_path)
    query = f"SELECT access_key_id, plan FROM cloud_accounts WHERE account_id = '{account_id}'"
    return conn.execute(query).fetchall()
