import sqlite3
import random 
from typing import Literal, Callable, TypeVar, ParamSpec
from functools import wraps
 
P = ParamSpec("P")
R = TypeVar("R") 
 
 
def db_connect(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args, **kwargs):
        con = sqlite3.connect("db.db")
        cur = con.cursor()
        try:
            result = func(cur, *args, **kwargs)
            con.commit()
        except Exception as e:
            con.rollback()
            print(f"ОШИБКА: {e}")
        finally:
            con.close()
        return result
    return wrapper
 
@db_connect
def create_table(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
        player_id INTEGER UNIQUE,
        username TEXT,
        role TEXT,
        mafia_vote INTEGER,
        citizen_vote INTEGER,
        voted INTEGER,
        dead INTEGER
    )""")
 
@db_connect
def insert_player(cur, player_id: int, username: str) -> None:
    sql = "INSERT INTO players (player_id, username, mafia_vote, citizen_vote, voted, dead) \
    VALUES (?, ?, ?, ?, ?, ?)"
    cur.execute(sql, (player_id, username, 0, 0, 0, 0))
 
 
@db_connect
def players_amount(cur) -> int:
    sql = "SELECT * FROM players"
    cur.execute(sql)
    res = cur.fetchall() # fetchall() [("asdasdas",), ("sdasadsad",), ] fetchone() ("asdasdas",)
    return len(res)
 
@db_connect
def get_mafia_usernames(cur) -> str:
    sql = "SELECT username FROM players WHERE role = 'mafia' "
    cur.execute(sql)
    data = cur.fetchall()
    names = ""
    for row in data: # [("asdasdas",), ("sdasadsad",), ]
        name = row[0]
        names += name + "\n"
    return names
 
@db_connect
def get_players_roles(cur) -> list:
    sql = "SELECT player_id, role FROM players"
    cur.execute(sql)
    data = cur.fetchall()
    return data
 
@db_connect
def get_all_alive(cur) -> list[str]:
    sql = "SELECT username FROM players WHERE dead=0"
    cur.execute(sql)
    data = cur.fetchall() # [("Никита",), ("Артём",), ("Михаил",)]
    data = [row[0] for row in data]
    return data
 
@db_connect
def set_roles(cur, players: int) -> None:
    game_roles = ["citizen"] * players # ["citizen", "citizen", "citizen", "citizen", "citizen", "citizen"]
    mafias = int(players * 0.3)
    for i in range(mafias):
        game_roles[i] = "mafia" # ["mafia", "citizen", "citizen", "citizen", "citizen", "citizen"]
    random.shuffle(game_roles) # ["citizen", "citizen", "mafia", "citizen", "citizen", "citizen"]
    cur.execute("SELECT player_id FROM players")
    player_ids = cur.fetchall() # [(0,), (1,), (2,)] 
    for role, player_id in zip(game_roles, player_ids): # [('citizen', (0,)), ('mafia', (1,)), ('citizen', (2,))]
        sql = "UPDATE players SET role=? WHERE player_id=?"
        cur.execute(sql, (role, player_id[0]))
 
@db_connect
def vote(cur, type: Literal["mafia_vote", "citizen_vote"], username: str, player_id: int) -> bool:
    cur.execute("SELECT username FROM players WHERE player_id=? AND dead=0 AND voted=0", (player_id,))
    can_vote = cur.fetchone()
    if can_vote:
        cur.execute(f"UPDATE players SET {type} = {type} + 1 WHERE username=?", (username,))
        cur.execute("UPDATE players SET voted=1 WHERE player_id=?", (player_id,))
        return True
    return False
 
@db_connect
def mafia_kill(cur) -> str:
    cur.execute("SELECT MAX(mafia_vote) FROM players")
    max_votes = cur.fetchone()[0] # (10,)
    cur.execute("SELECT COUNT(*) FROM players WHERE dead=0 AND role='mafia'")
    mafia_alive = cur.fetchone()[0]
    killed = "никого"
    if max_votes == mafia_alive:
        cur.execute("SELECT username FROM players WHERE mafia_vote=?", (max_votes,))
        killed = cur.fetchone()[0] # ("Артём",)
        cur.execute("UPDATE players SET dead=1 WHERE username=?", (killed,))
    return killed
 
@db_connect
def citizen_kill(cur) -> str:
    cur.execute("SELECT MAX(citizen_vote) FROM players")
    max_votes = cur.fetchone()[0] # (10,)
    cur.execute("SELECT COUNT(*) FROM players WHERE citizen_vote=?", (max_votes,))
    max_count = cur.fetchone()[0]
    killed = "никого"
    if max_count == 1:
        cur.execute("SELECT username FROM players WHERE citizen_vote=?", (max_votes,))
        killed = cur.fetchone()[0]
        cur.execute("UPDATE players SET dead=1 WHERE username=?", (killed,))
    return killed
 
@db_connect
def check_winner(cur) -> str | None:
    cur.execute("SELECT COUNT(*) FROM players WHERE role='mafia' AND dead=0")
    mafia_alive = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE role!='mafia' AND dead=0")
    citizen_alive = cur.fetchone()[0]
    if mafia_alive > citizen_alive:
        return "Мафия"
    elif mafia_alive == 0:
        return "Горожане"
    return None
 
@db_connect
def clear(cur, dead: bool=False) -> None:
    sql = "UPDATE players SET citizen_vote=0, mafia_vote=0, voted=0"
    if dead:
        sql += ", dead=0"
    cur.execute(sql)
 
 
if __name__ == "__main__":
    create_table()
    # insert_player(1, "Артём")
    # insert_player(2, "Никита")
    # insert_player(3, "Максим")
    # insert_player(4, "Алёна")
    # insert_player(5, "Илья")
    # insert_player(6, "Матвей")
    # print(players_amount())
    # print(get_mafia_usernames())
    # print(get_players_roles())
    # print(get_all_alive())
    # set_roles(players_amount())
    # print(get_players_roles())
    # print(vote("mafia_vote", "Артём", 2))
    # print(vote("citizen_vote", "Никита", 1))
    # print(vote("mafia_vote", "Максим", 5))
    # print(vote("citizen_vote", "Илья", 4))
    print(mafia_kill())
    print(citizen_kill())