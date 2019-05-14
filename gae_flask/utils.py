def get_game_info(conn, game):
    # get the basic game properties
    cursor = conn.cursor()
    cursor.execute("SELECT player1,player2,size,state FROM games WHERE id = %s;", (game,))

    if cursor.rowcount == 0:
        print("ERROR: Invalid game ID: id=%d" % (game))
        TODO

    if cursor.rowcount > 1:
        print("ERROR: Too many rows in the SELECT output!  id=%d  cursor.rowcount=%d" % (game,cursor.rowcount))
    row = cursor.fetchall()[0]

    cursor.close()

    players = [row[0],row[1]]
    size    =  row[2]
    state   =  row[3]

    if state is None:
         state = "Active"

    return (players,size,state)



def build_board(conn, game,size):
    # we'll build the empty board, and then fill in with the move list that
    # we get from the DB.
    board = []
    for i in range(size):
        board.append([""]*size)


    # search for all moves that have happenend during this game.
    cursor = conn.cursor()
    cursor.execute("SELECT x,y,letter FROM moves WHERE gameID = %s;", (game,))

    counts = {"X":0, "O":0}
    for move in cursor.fetchall():
        (x,y,letter) = move

        x = int(x)
        y = int(y)
        assert x >= 0 and x < size
        assert y >= 0 and y < size

        assert letter in "XO"

        assert board[x][y] == ""
        board[x][y] = letter

        counts[letter] += 1

    cursor.close()

    assert counts["X"] >= counts["O"]
    assert counts["X"] <= counts["O"]+1

    if counts["X"] == counts["O"]:
        nextPlayer = 0
    else:
        nextPlayer = 1
    letter = "XO"[nextPlayer]

    return (board,nextPlayer,letter)



def analyze_board(board):
    size = len(board)

    for x in range(size):
        # scan through the column 'x' to see if they are all the same.
        if board[x][0] == "":
            continue
        all_same = True
        for y in range(1,size):
            if board[x][y] != board[x][0]:
                all_same = False
                break
        if all_same:
            return "win"

    for y in range(size):
        # scan through the row 'y' to see if they are all the same.
        if board[0][y] == "":
            continue
        all_same = True
        for x in range(1,size):
            if board[x][y] != board[0][y]:
                all_same = False
                break
        if all_same:
            return "win"

    # check the NW/SE diagonal
    if board[0][0] != "":
        all_same = True
        for i in range(1,size):
            if board[i][i] != board[0][0]:
                all_same = False
                break
        if all_same:
            return "win"

    # check the NE/SW diagonal
    if board[size-1][0] != "":
        all_same = True
        for i in range(1,size):
            if board[size-1-i][i] != board[size-1][0]:
                all_same = False
                break
        if all_same:
            return "win"

    # check for stalemate
    for x in range(size):
        for y in range(size):
            if board[x][y] == "":
                return ""
    return "stalemate"


