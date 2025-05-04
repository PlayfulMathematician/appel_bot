import sqlite3

DB_PATH = "starboard.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS starboard (
            message_id INTEGER PRIMARY KEY,
            star_message_id INTEGER,
            embed_message_id INTEGER,
            channel_id INTEGER,
            guild_id INTEGER,
            author_id INTEGER,
            reaction_count INTEGER
        )
        ''')
        conn.commit()
def add_starred_message(message_id, star_message_id, embed_message_id, channel_id, guild_id, author_id, reaction_count):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO starboard (message_id, star_message_id, embed_message_id, channel_id, guild_id, author_id, reaction_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (message_id, star_message_id, embed_message_id, channel_id, guild_id, author_id, reaction_count))
        conn.commit()
def remove_starred_message(message_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        DELETE FROM starboard WHERE message_id = ?
        ''', (message_id,))
        conn.commit()
def get_starred_message(message_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM starboard WHERE message_id = ?
        ''', (message_id,))
        return cursor.fetchone()
def update_reaction_count(message_id, reaction_count):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE starboard SET reaction_count = ? WHERE message_id = ?
        ''', (reaction_count, message_id))
        conn.commit()
def get_all_starred_messages():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM starboard')
        return cursor.fetchall()
    