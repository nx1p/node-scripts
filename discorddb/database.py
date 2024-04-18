import sqlite3

def create_tables():
    conn = sqlite3.connect('discord_data.db')
    c = conn.cursor()

    # Create servers table
    c.execute('''CREATE TABLE IF NOT EXISTS servers
                 (id TEXT PRIMARY KEY, name TEXT)''')

    # Create channels table
    c.execute('''CREATE TABLE IF NOT EXISTS channels
                 (id TEXT PRIMARY KEY, name TEXT, server_id TEXT,
                  type TEXT, FOREIGN KEY (server_id) REFERENCES servers (id))''')

    # Create threads table
    c.execute('''CREATE TABLE IF NOT EXISTS threads
                 (id TEXT PRIMARY KEY, name TEXT, parent_channel_id TEXT,
                  FOREIGN KEY (parent_channel_id) REFERENCES channels (id))''')

    # Create messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id TEXT PRIMARY KEY, content TEXT, author_id TEXT,
                  timestamp TEXT, channel_id TEXT, is_thread_message INTEGER,
                  FOREIGN KEY (channel_id) REFERENCES channels (id),
                  FOREIGN KEY (channel_id) REFERENCES threads (id))''')

    conn.commit()
    conn.close()
