"""
Migration script: restructure DB for template-based report generation.

Changes:
1. indicators table: add parent_id, is_leaf, update system values
2. indicator_question table: remove parent-node mappings (keep leaf-only)
3. reports table: rename columns, add persona_template_id
4. Create persona_templates table
5. Create indicator_texts table
"""
import json
import sys
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Resolve DB path
API_DIR = Path(__file__).resolve().parent.parent
DB_PATH = API_DIR / "mindwise.db"
SEED_DIR = API_DIR / "tools" / "initial_db_tool"

if not DB_PATH.exists():
    print(f"❌ Database not found at {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(str(DB_PATH))
conn.execute("PRAGMA foreign_keys = OFF")
cur = conn.cursor()


def table_has_column(table: str, column: str) -> bool:
    cols = [row[1] for row in cur.execute(f"PRAGMA table_info({table})").fetchall()]
    return column in cols


def table_exists(table: str) -> bool:
    return cur.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()[0] > 0


# ── 1. Alter indicators table ──────────────────────────────
print("── Migrating indicators table ──")
if not table_has_column("indicators", "parent_id"):
    cur.execute("ALTER TABLE indicators ADD COLUMN parent_id INTEGER REFERENCES indicators(id)")
    print("  Added parent_id column")
if not table_has_column("indicators", "is_leaf"):
    cur.execute("ALTER TABLE indicators ADD COLUMN is_leaf INTEGER NOT NULL DEFAULT 1")
    print("  Added is_leaf column")

# Update indicator data
with open(SEED_DIR / "default_indicators.json", encoding="utf-8") as f:
    indicators = json.load(f)

for ind in indicators:
    cur.execute(
        "UPDATE indicators SET system=?, parent_id=?, is_leaf=? WHERE id=?",
        (ind["system"], ind["parent_id"], ind["is_leaf"], ind["id"]),
    )
print(f"  Updated {len(indicators)} indicator records (system, parent_id, is_leaf)")

# ── 2. Clean indicator_question table ─────────────────────
print("── Cleaning indicator_question table ──")
parent_ids = [ind["id"] for ind in indicators if ind["is_leaf"] == 0]
if parent_ids:
    placeholders = ",".join("?" * len(parent_ids))
    deleted = cur.execute(
        f"DELETE FROM indicator_question WHERE indicator_id IN ({placeholders})", parent_ids
    ).rowcount
    print(f"  Removed {deleted} parent-node mappings")
remaining = cur.execute("SELECT COUNT(*) FROM indicator_question").fetchone()[0]
print(f"  Remaining leaf-only mappings: {remaining}")

# ── 3. Create persona_templates table ─────────────────────
print("── Creating persona_templates table ──")
if not table_exists("persona_templates"):
    cur.execute("""
        CREATE TABLE persona_templates (
            id INTEGER PRIMARY KEY,
            code VARCHAR(10) NOT NULL UNIQUE,
            motivation_level VARCHAR(1) NOT NULL,
            regulation_level VARCHAR(1) NOT NULL,
            execution_level VARCHAR(1) NOT NULL,
            teacher_label VARCHAR(100) NOT NULL,
            teacher_description TEXT NOT NULL,
            student_label VARCHAR(100) NOT NULL,
            student_description TEXT NOT NULL
        )
    """)
    with open(SEED_DIR / "default_persona_templates.json", encoding="utf-8") as f:
        personas = json.load(f)
    for p in personas:
        cur.execute(
            "INSERT INTO persona_templates (id, code, motivation_level, regulation_level, execution_level, teacher_label, teacher_description, student_label, student_description) VALUES (?,?,?,?,?,?,?,?,?)",
            (p["id"], p["code"], p["motivation_level"], p["regulation_level"], p["execution_level"],
             p["teacher_label"], p["teacher_description"], p["student_label"], p["student_description"]),
        )
    print(f"  Created and seeded {len(personas)} persona templates")
else:
    print("  persona_templates already exists, skipping")

# ── 4. Create indicator_texts table ─────────��─────────────
print("─��� Creating indicator_texts table ──")
if not table_exists("indicator_texts"):
    cur.execute("""
        CREATE TABLE indicator_texts (
            id INTEGER PRIMARY KEY,
            indicator_id INTEGER NOT NULL REFERENCES indicators(id),
            level VARCHAR(1) NOT NULL,
            view VARCHAR(10) NOT NULL,
            analysis TEXT NOT NULL,
            suggestion TEXT NOT NULL,
            golden_quote TEXT
        )
    """)
    print("  Created indicator_texts table (empty — needs content)")
else:
    print("  indicator_texts already exists, skipping")

# ── 5. Alter reports table ────────────────────────────────
print("── Migrating reports table ──")
if not table_has_column("reports", "persona_template_id"):
    cur.execute("ALTER TABLE reports ADD COLUMN persona_template_id INTEGER REFERENCES persona_templates(id)")
    print("  Added persona_template_id column")
if not table_has_column("reports", "motivation_level"):
    cur.execute("ALTER TABLE reports ADD COLUMN motivation_level VARCHAR(1)")
    print("  Added motivation_level column")
if not table_has_column("reports", "regulation_level"):
    cur.execute("ALTER TABLE reports ADD COLUMN regulation_level VARCHAR(1)")
    print("  Added regulation_level column")
if not table_has_column("reports", "execution_level"):
    cur.execute("ALTER TABLE reports ADD COLUMN execution_level VARCHAR(1)")
    print("  Added execution_level column")

# Migrate old column data if exists
if table_has_column("reports", "motivational_system"):
    print("  Note: old columns (motivational_system, etc.) still exist — safe to ignore")

# ── 6. Clean score_student — remove parent indicator scores ──
print("── Cleaning score_student table ──")
if parent_ids:
    placeholders = ",".join("?" * len(parent_ids))
    deleted = cur.execute(
        f"DELETE FROM score_student WHERE indicator_id IN ({placeholders})", parent_ids
    ).rowcount
    print(f"  Removed {deleted} parent-node score records")

conn.commit()
conn.close()
print("\n🎉 Migration complete!")
