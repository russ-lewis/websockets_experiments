# DERIVED FROM GOOGLE'S WEBSOCKET GAE EXAMPLE
#     https://cloud.google.com/appengine/docs/flexible/python/using-websockets-and-session-affinity
#     git clone https://github.com/GoogleCloudPlatform/python-docs-samples


from flask         import Flask, request, render_template, redirect, url_for
from flask_sockets import Sockets

import MySQLdb
import private_no_share_dangerous_passwords as pnsdp

import utils



app       = Flask(__name__)
ws_server = Sockets(app)



# connect to the database
def open_db():
    return MySQLdb.connect(host   = pnsdp.SQL_HOST,
                           user   = pnsdp.SQL_USER,
                           passwd = pnsdp.SQL_PASSWD,
                           db     = pnsdp.SQL_DB)



@app.route("/")
def index():
    print("TODO: implement the full index lookup!")
    return render_template("index.html");


@app.route("/game.html")
def game():
    # read the HTTP parameters
    if "user" not in request.values or "game" not in request.values:
        TODO
    game = int(request.values["game"])
    user = request.values["user"]


    # connect to the database, then read the game state
    conn = open_db()

    (players,size,state)       = utils.get_game_info(conn, game)
    (board, nextToPlay,letter) = utils.build_board(conn, game,size)

    return render_template("game.html",
                           gameID=game,
                           players=players,
                           size=3,
                           nextToPlay=players[nextToPlay],
                           thisPlayer=user,
                           state=state,
                           board=board,
                           canPlay=(nextToPlay == user))


@app.route("/move", methods=["POST"])
def move():
    if "user" not in request.values or "game" not in request.values:
        TODO
    if "pos" not in request.values and "resign" not in request.values:
        TODO


    # connect to the database
    conn = open_db()


    game = int(request.values["game"])
    (players,size,state) = utils.get_game_info(conn, game)

    print("game_info:", (players,size,state))

    user = request.values["user"]
    if user not in players:
        TODO


    if "resign" in request.values:
        resign = True
    else:
        resign = False
        pos = request.values["pos"].split(",")
        assert len(pos) == 2
        x = int(pos[0])
        y = int(pos[1])


    (board,nextPlayer,letter) = utils.build_board(conn, game,size)

    if user != players[nextPlayer]:
        TODO


    if resign:
        # this user is choosing to resign.  Update the game state to reflect that.
        other_player_name = players[1-nextPlayer]

        cursor = conn.cursor()
        cursor.execute("""UPDATE games SET state=%s WHERE id=%s;""", (other_player_name+":resignation",game))
        cursor.close()

    else:
        assert x >= 0 and x < size
        assert y >= 0 and y < size

        assert board[x][y] == ""
        board[x][y] = "XO"[nextPlayer]

        # we've done all of our sanity checks.  We now know enough to say that
        # it's safe to add a new move.
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO moves(gameID,x,y,letter,time) VALUES(%s,%s,%s,%s,NOW());""", (game,x,y,letter))

        if cursor.rowcount != 1:
            TODO

        cursor.close()

        result = utils.analyze_board(board)
        if result != "":
            if result == "win":
                result = players[nextPlayer]+":win"

            cursor = conn.cursor()
            cursor.execute("""UPDATE games SET state=%s WHERE id=%s;""", (result,game))
            cursor.close()

    # we've made changes, make sure to commit them!
    conn.commit()
    conn.close()


    # Redirect to a GET operation.  This is the POST/REDIRECT/GET pattern.
    return redirect("%s?game=%d&user=$s" % (url_for("game"), game, user),
                    code=303)







# ----------------------------------------------------------------------------------------- # 
#                                                                                           #
#                                  Start websocket server                                   #
#                                                                                           #
# ----------------------------------------------------------------------------------------- # 

# this is a dictionary of websockets, where the key is the gameID that is being
# watched, and the value is a set of websockets.  When *anything* happens on a
# given game, we will automatically send a single message (with the gameID as
# the entire payload) to any interested websockets.  They will then drive an
# HTTP request to reload the game state.
notifyTables = {}



import random

@ws_server.route("/ws")
def ws_server(socket):
    global notifyTables

    dummy = random.randint(0,999)
    print("New socket!  dummy: %d" % dummy)

    msg = socket.receive()
    if msg is None:
        return

    try:
        gameID = int(msg)
        print("dummy %d : gameID = %d" % (dummy,gameID))
    except:
        print("Received invalid message, len=%d.  First 20 characters: '%s'" % (len(msg), msg[:20]))
        return

    # add the socket to the proper slot in the notifyTables.  Then we'll just
    # enter a dummy read loop; we don't expect to *EVER* have anything come
    # in, but it allows us to keep this function open (on the theory that,
    # probably, flask_sockets will close the socket if we return).
    if gameID in notifyTables:
        notifyTables[gameID].add(socket)
    else:
        notifyTables[gameID] = set([socket])

    while not socket.closed:
        msg = socket.receive()
        if msg is None:
            continue
        print("Spurious recv with dummy %d gameID %d : payload='%s'" % (dummy,gameID, msg))


