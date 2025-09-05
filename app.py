# app.py — Advanced QuickList (Streamlit + SQLite)
import streamlit as st
from datetime import date, datetime
from uuid import uuid4
import sqlite3
import pandas as pd

# ----------------------------
# Database (SQLite) utilities
# ----------------------------
DB_PATH = "quicklist.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        tag TEXT,
        due TEXT,
        priority TEXT,
        done INTEGER DEFAULT 0,
        created_at TEXT,
        parent_id TEXT
    )
    """)
    conn.commit()
    return conn

conn = init_db()

def add_task(title, tag="", due="", priority="normal", parent_id=None):
    cur = conn.cursor()
    tid = str(uuid4())[:8]
    cur.execute(
        "INSERT INTO tasks (id, title, tag, due, priority, done, created_at, parent_id) VALUES (?, ?, ?, ?, ?, 0, ?, ?)",
        (tid, title, tag, due, priority, datetime.utcnow().isoformat(), parent_id),
    )
    conn.commit()
    return tid

def update_task(tid, **fields):
    cur = conn.cursor()
    keys = ", ".join([f"{k}=?" for k in fields.keys()])
    values = list(fields.values()) + [tid]
    cur.execute(f"UPDATE tasks SET {keys} WHERE id = ?", values)
    conn.commit()

def delete_task(tid):
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (tid,))
    # delete subtasks too
    cur.execute("DELETE FROM tasks WHERE parent_id = ?", (tid,))
    conn.commit()

def list_tasks():
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    return [dict(r) for r in cur.fetchall()]

def export_tasks_df():
    rows = list_tasks()
    return pd.DataFrame(rows)

def clear_completed():
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE done = 1")
    conn.commit()

# ----------------------------
# Helper utilities
# ----------------------------
def parse_date_iso(d):
    if not d:
        return None
    try:
        return datetime.fromisoformat(d).date()
    except Exception:
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            return None

def fmt_date(diso):
    d = parse_date_iso(diso)
    return d.strftime("%b %d") if d else ""

def is_overdue(diso):
    d = parse_date_iso(diso)
    return d and d < date.today()

# ----------------------------
# Streamlit App UI
# ----------------------------
st.set_page_config(page_title="QuickList — Advanced", page_icon="✅", layout="wide")
st.title("QuickList — Advanced ✅")
st.write("Persistent to-do app (SQLite) • Subtasks • CSV import/export • Search & sort")

# --- Left column: Add task / Controls
left, right = st.columns([3, 7])

with left:
    with st.expander("Add task", expanded=True):
        with st.form("add_task"):
            t_col, tag_col, due_col, pri_col = st.columns([4, 2, 2, 2])
            title = t_col.text_input("Task title", placeholder="e.g., Finish OutlineIQ README")
            tag = tag_col.text_input("Tag (optional)", placeholder="project,study")
            due_date = due_col.date_input("Due date (optional)", value=None)
            priority = pri_col.selectbox("Priority", ["normal", "high", "low"], index=0)
            parent = st.selectbox("Parent task (optional, for subtasks)", options=["None"] + [f"{r['id']} — {r['title']}" for r in list_tasks()], index=0)
            submitted = st.form_submit_button("Add Task")
            if submitted and title.strip():
                due_iso = due_date.isoformat() if isinstance(due_date, date) else ""
                parent_id = None if parent == "None" else parent.split(" — ")[0]
                add_task(title.strip(), tag.strip(), due_iso, priority, parent_id)
                st.success("Task added")
                st.rerun()

    with st.expander("Bulk actions"):
        if st.button("Clear completed tasks"):
            clear_completed()
            st.success("Cleared completed tasks")
            st.rerun()

        uploaded = st.file_uploader("Import tasks from CSV (columns: title,tag,due,priority,parent_id)", type=["csv"])
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                created = 0
                for _, row in df.iterrows():
                    title = str(row.get("title", "")).strip()
                    if not title:
                        continue
                    add_task(title, str(row.get("tag", "")).strip(), str(row.get("due", "")).strip(), str(row.get("priority", "normal")).strip(), str(row.get("parent_id", None)).strip() or None)
                    created += 1
                st.success(f"Imported {created} tasks")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

        df_export = export_tasks_df()
        to_csv = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("Export tasks to CSV", to_csv, file_name="quicklist_tasks.csv", mime="text/csv")

# --- Right column: Filters, Search, and Task list
with right:
    f1, f2, f3, f4 = st.columns([4, 2, 2, 3])
    q = f1.text_input("Search tasks (title or tag)")
    tags = sorted({(t["tag"] or "").strip() for t in list_tasks() if (t.get("tag") or "").strip()})
    tag_filter = f2.selectbox("Filter by tag", options=["All"] + tags, index=0)
    sort_choice = f3.selectbox("Sort by", ["created (new→old)", "due (near→far)", "priority (high→low)"])
    view_choice = f4.selectbox("View", ["All tasks", "Top-level tasks only", "Subtasks only"])

    tasks = list_tasks()

    if q:
        qlow = q.lower().strip()
        tasks = [t for t in tasks if qlow in (t["title"] or "").lower() or qlow in (t.get("tag") or "").lower()]

    if tag_filter != "All":
        tasks = [t for t in tasks if (t.get("tag") or "").strip() == tag_filter]

    if view_choice == "Top-level tasks only":
        tasks = [t for t in tasks if not t.get("parent_id")]
    elif view_choice == "Subtasks only":
        tasks = [t for t in tasks if t.get("parent_id")]

    if sort_choice == "due (near→far)":
        def due_sort_key(t):
            d = parse_date_iso(t.get("due") or "")
            return (d or date.max)
        tasks = sorted(tasks, key=due_sort_key)
    elif sort_choice == "priority (high→low)":
        order = {"high": 0, "normal": 1, "low": 2}
        tasks = sorted(tasks, key=lambda x: order.get(x.get("priority","normal"), 1))
    else:
        tasks = sorted(tasks, key=lambda x: x.get("created_at") or "", reverse=True)

    total = len(list_tasks())
    done_cnt = sum(1 for t in list_tasks() if t["done"])
    overdue_cnt = sum(1 for t in list_tasks() if is_overdue(t.get("due")))
    st.markdown(f"**Stats:** Total: {total} • Done: {done_cnt} • Overdue: {overdue_cnt}")

    top_tasks = [t for t in tasks if not t.get("parent_id")]
    id_to_task = {t["id"]: t for t in tasks}

    def render_task_card(t):
        col1, col2, col3, col4, col5 = st.columns([0.5, 5, 1.5, 1, 1])
        done_key = f"done_{t['id']}"
        title_key = f"title_{t['id']}"
        checked = col1.checkbox("", value=bool(t["done"]), key=done_key)
        if checked != bool(t["done"]):
            update_task(t["id"], done=1 if checked else 0)
            st.rerun()
        new_title = col2.text_input("", value=t["title"], key=title_key, label_visibility="collapsed")
        meta = " • ".join(filter(None, [
            f"#{t['tag']}" if t.get("tag") else "",
            "High" if t.get("priority")=="high" else ("Low" if t.get("priority")=="low" else ""),
            ("Due " + fmt_date(t.get("due"))) if t.get("due") else ""
        ]))
        if is_overdue(t.get("due")) and not t["done"]:
            col2.markdown(f"**<span style='color:#ff6b6b'>{new_title}</span>**", unsafe_allow_html=True)
            col2.caption(meta)
        else:
            col2.write(new_title)
            col2.caption(meta or "No meta")
        pr = col3.selectbox("Priority", ["normal","high","low"], index=["normal","high","low"].index(t.get("priority","normal")), key=f"pri_{t['id']}")
        if pr != t.get("priority"):
            update_task(t["id"], priority=pr)
            st.rerun()
        if col4.button("Save", key=f"save_{t['id']}"):
            update_task(t["id"], title=new_title.strip() or t["title"])
            st.success("Saved")
            st.rerun()
        if col5.button("Delete", key=f"del_{t['id']}"):
            delete_task(t["id"])
            st.success("Deleted")
            st.rerun()

    if not top_tasks:
        st.info("No tasks match your filters.")
    else:
        for t in top_tasks:
            st.markdown("---")
            render_task_card(t)
            subtasks = [s for s in tasks if s.get("parent_id") == t["id"]]
            if subtasks:
                with st.expander(f"Subtasks ({len(subtasks)})", expanded=False):
                    for s in subtasks:
                        render_task_card(s)

    st.markdown("---")
    st.caption("Tip: use CSV export to back up tasks. This app stores tasks in a local SQLite file (quicklist.db).")
