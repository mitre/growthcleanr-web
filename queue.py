from huey import SqliteHuey


huey_queue = SqliteHuey(filename="huey_queue.db")
