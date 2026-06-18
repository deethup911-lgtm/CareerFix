import sqlite3
import hashlib
import os
import threading
import numpy as np

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(base_dir, 'data', 'embedding_cache.db')

# Module-level lock so concurrent threads don't corrupt writes
_lock = threading.Lock()

# Sentinel: DB is initialized only once per process lifetime
_db_initialized = False


def create_cache_db():
    """Initializes the SQLite database and the embeddings table."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            content_hash TEXT PRIMARY KEY,
            original_text TEXT,
            embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def _ensure_db():
    """Initialises the DB exactly once per process. Thread-safe via the module lock."""
    global _db_initialized
    if not _db_initialized:
        with _lock:
            # Double-checked locking: another thread may have beaten us here.
            if not _db_initialized:
                create_cache_db()
                _db_initialized = True


def get_text_hash(text):
    """Generates SHA256 hash from target text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def get_cached_embedding(content_hash):
    """Retrieves cached embedding if exists, otherwise returns None."""
    _ensure_db()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT embedding FROM embeddings WHERE content_hash = ?", (content_hash,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if row:
        emb_bytes = row[0]
        # Convert raw byte array back to float32 numpy array
        return np.frombuffer(emb_bytes, dtype=np.float32)
    return None


def save_embedding(content_hash, original_text, embedding):
    """Saves embedding array as binary BLOB in SQLite. Thread-safe."""
    _ensure_db()
    if not isinstance(embedding, np.ndarray):
        embedding = np.array(embedding, dtype=np.float32)
    else:
        embedding = embedding.astype(np.float32)

    emb_bytes = embedding.tobytes()

    with _lock:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO embeddings (content_hash, original_text, embedding) VALUES (?, ?, ?)",
                (content_hash, original_text, emb_bytes)
            )
            conn.commit()
        finally:
            conn.close()


def get_or_create_embedding(text, model):
    """High-level utility to get from cache or encode and save."""
    content_hash = get_text_hash(text)
    cached = get_cached_embedding(content_hash)
    if cached is not None:
        print(f"[CACHE HIT] Found cached embedding for hash: {content_hash[:8]}")
        return cached

    print(f"[CACHE MISS] Encoding new text for hash: {content_hash[:8]}")
    emb_tensor = model.encode(text, convert_to_tensor=True)

    # Check if tensor or numpy
    if hasattr(emb_tensor, 'cpu'):
        emb_np = emb_tensor.cpu().numpy()
    else:
        emb_np = np.array(emb_tensor, dtype=np.float32)

    save_embedding(content_hash, text, emb_np)
    return emb_np


def get_cache_stats():
    """Retrieves cache stats: total cached, db path, and db size."""
    _ensure_db()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total_cached = cursor.fetchone()[0]
    finally:
        conn.close()

    db_size = 0
    if os.path.exists(DB_PATH):
        db_size = os.path.getsize(DB_PATH)

    return {
        "total_cached_embeddings": total_cached,
        "database_path": DB_PATH,
        "database_size_bytes": db_size
    }


def clear_cache():
    """Truncates the embeddings cache table."""
    _ensure_db()
    with _lock:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM embeddings")
            conn.commit()
        finally:
            conn.close()
    print("[CACHE] Embedded cache cleared successfully.")
