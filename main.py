# -*- coding: utf-8 -*-
from termcolor import colored
from prettytable import PrettyTable
import json, sys, random

automated = False

log_prefix = "json_log/game_"
turn_counter = 0

things = {
    "a": "OBERST VON GATOW",
    "b": "PROFESSOR BLOOM",
    "c": "REVEREND GRÜN",
    "d": "BARONIN VON PORZ",
    "e": "FRÄULEIN GLORIA",
    "f": "FRAU WEISS",

    "u": "DOLCH",
    "v": "LEUCHTER",
    "w": "PISTOLE",
    "x": "SEIL",
    "y": "HEIZUNGSROHR",
    "z": "ROHRZANGE",

    "1": "HALLE",
    "2": "SALON",
    "3": "SPEISEZIMMER",
    "4": "KÜCHE",
    "5": "MUSIKZIMMER",
    "6": "WINTERGARTEN",
    "7": "BILLIARDZIMMER",
    "8": "BIBLIOTHEK",
    "9": "ARBEITSZIMMER"
}

# things = {
#     "a": "MUSTARD",
#     "b": "ORCHID",
#     "c": "GREEN",
#     "d": "PEACOCK",
#     "e": "SCARLET",
#     "f": "PLUM",
#
#     "u": "CANDLESTICK",
#     "v": "DAGGER",
#     "w": "LEAD PIPE",
#     "x": "REVOLVER",
#     "y": "ROPE",
#     "z": "WRENCH",
#
#     "1": "HALL",
#     "2": "LOUNGE",
#     "3": "DINING ROOM",
#     "4": "KITCHEN",
#     "5": "BALLROOM",
#     "6": "CONSERVATORY",
#     "7": "BILLIARD ROOM",
#     "8": "LIBRARY",
#     "9": "STUDY"
# }
players = []
all_cards = ["a","b","c","d","e","f", "u","v","w","x","y","z", "1","2","3","4","5","6","7","8","9"]
groups = [["a","b","c","d","e","f"],["u","v","w","x","y","z"],["1","2","3","4","5","6","7","8","9"]]

maybes = {}
r = dict(things)
for key, value in r.items():
    r[key] = {}

def predict_answer(player, items):
    yes = False
    no = True
    for item in items:
        if r[item][player] == "y":
            yes = True
            no = False
        elif r[item][player] == "?":
            no = False
    if no:
        return color_value("n")
    elif yes:
        return color_value("y")
    else:
        return color_value("?")

def empty_row():
    l = []
    for x in range(len(players)+2):
        l.append("")
    return l

def color_value(v):
    if v == "y":
        v = colored(v,'green')
    elif v == "?":
        v = colored(v,'yellow')
    elif v == "n":
        v = colored(v, 'red')
    else:
        v = colored(v, 'purple')
    return v

def printtable():
    t = PrettyTable(["S","Thing"]+players)
    c = 0
    for key, item in things.items():
        row = [key]
        status = item_status(key)
        item_col = item
        if status == "owned":
            item_col = colored(item, 'green')
        elif status == "unknown":
            item_col = colored(item, 'yellow')
        elif status == "murder":
            item_col = colored(item, 'red')
            print("We know that %s is part of the solution." % item_col)
        row.append(item_col)
        for player in players:
            v = r[key][player]
            v = color_value(v)
            row.append(v)
        t.add_row(row)

        c+=1
        if c in [6,12]:
            t.add_row(empty_row())
    print(t)

def dump_json():
    all_the_info = {'players': players, 'n_cards': n_cards, 'my_items': my_items, 'r': r, 'maybes': maybes}
    text = json.dumps(all_the_info, ensure_ascii = False)
    file = open(log_prefix + my_items + "_" + str(turn_counter), 'w')
    file.write(text)
    file.close()

def printmaybes():
    t = PrettyTable(["Player","Maybe"])
    for player, m in maybes.items():
        t.add_row([player,m])
    print(t)

def set_has_item(player, item):
    pl = player
    for p in players:
        r[item][p] = "n"
    r[item][player] = "y"
    for player in players:
        del_list = []
        for maybe in maybes[player]:
            if item in maybe:
                if pl == player:
                    del_list.append((player,maybe))
                else:
                    maybe.remove(item)
                    if len(maybe) < 2:
                        del_list.append((player,maybe))
                        set_has_item(player,maybe[0])
        handle_maybe_del_list(del_list)

def handle_maybe_del_list(l):
    for i in l:
        if i[1] in maybes[i[0]]:
            maybes[i[0]].remove(i[1])
        print("already deleted")

def item_status(item):
    all_n = True
    owned = False
    i = r[item]
    for owner, status in i.items():
        if status == "y":
            all_n = False
            owned = True
        elif status != "n":
            all_n = False
    if all_n:
        return "murder"
    elif owned:
        return "owned"
    else:
        return "unknown"

def set_does_not_have_item(player, item):
    r[item][player] = "n"
    del_list = []
    for maybe in maybes[player]:
        if item in maybe:
            maybe.remove(item)
            if len(maybe) < 2:
                i = maybe[0]
                print("This resolves a maybe for %s about item %s, we now know that they have it." % (player,i))
                del_list.append((player,i))
                set_has_item(player,i)
    handle_maybe_del_list(del_list)

def get_players_from_here(player):
    index = players.index(player) + 1
    return (players[index:]+players[:index])[:-1]

def fix_solved_group(group):
    i = []
    for item in group:
        c = 0
        o = None
        for owner, status in r[item].items():
            if status == "?":
                c += 1
                o = owner
            elif status == "y":
                c = -100
        if c == 1:
            set_has_item(o,item)
            print("%s must have %s because group %s was solved." %(o,item,group))

def get_card_lists():
    unknown = []
    murder = []
    for group in groups:
        for item in group:
            s = item_status(item)
            if s == "murder":
                murder.append(item)
            elif s == "unknown":
                unknown.append(item)
    return unknown, murder

def perform_check():
    for player in players:
        for card in has[player]:
            if r[card][player] == "n":
                print(player,card)
                print(has)
                print("solution",solution)
                input("Error")

def check_cards(): #called every round, to make decisions based on the known distribution of the cards
    murder = []
    for group in groups:
        n_owned = 0
        solved = False
        unknown = []
        for item in group:
            s = item_status(item)
            if s == "owned":
                n_owned += 1
            elif s == "murder":
                murder.append(item)
                solved = True
                fix_solved_group(group)
            elif s == "unknown":
                unknown.append(item)
        if n_owned == len(group) - 1 and solved == False and len(unknown) == 1:
            for player in players:
                set_does_not_have_item(player, unknown[0])
            print("All items except one in group %s are seen, it must be part of the solution." % group)
            fix_solved_group(group)
    if automated:
        if len(murder) > 2:
            printtable()
            printmaybes()
            print("has",has)
            print("solution",solution)
            print("Okay?", set(murder)==set(solution))
            if set(murder)==set(solution):
                sys.exit()
            else:
                input("Error")

    owned_cards = {}
    missing_cards = {}
    for player in players:
        owned_cards[player] = []
        missing_cards[player] = []
    for item, pl in r.items():
        for player in players:
            if pl[player] == "y":
                owned_cards[player].append(item)
            elif pl[player] == "?":
                missing_cards[player].append(item)
    for player in players:
        if len(missing_cards[player]) > 0:
            # print(player,"m",len(missing_cards[player]),"o",len(owned_cards[player]),"n",n_cards[player])
            # print(len(owned_cards[player]) == n_cards[player])
            # print(len(missing_cards[player]) + len(owned_cards[player]) == n_cards[player])
            if len(owned_cards[player]) == n_cards[player]: #we know all the cards he has, so he can't have the others with "?"
                print("%s can't have any more cards, setting the others to 'n'" % player)
                for card in missing_cards[player]:
                    set_does_not_have_item(player,card)
            elif len(missing_cards[player]) + len(owned_cards[player]) == n_cards[player]: #he must have all the cards we don't know about
                print("%s must have the other cards, setting them to 'y'" % player)
                for card in missing_cards[player]:
                    set_has_item(player, card)
        if len(missing_cards[player]) - n_cards[player] == 1 and len(maybes[player]) > 1:
            in_all_maybes = True
            card = missing_cards[player][0]
            for maybe in maybes[player]:
                if not card in maybe:
                    in_all_maybes = False
            if in_all_maybes:
                set_has_item(player, card)
                print(player, "only misses", card, "and it is in all maybes, so they must have it")
                check_cards
if len(sys.argv) > 1:
    if sys.argv[1] == "auto":
        automated = True
        print("Setting up saged game…")
        to_d = all_cards
        players = ["A","B","C","D","E"]
        n_cards = {"A":3,"B":4,"C":4,"D":3,"E":4}
        turn_counter = 0
        has = {}
        solution = []
        for group in groups:
            c = random.choice(group)
            solution.append(c)
            to_d.remove(c)
        counter = 0
        for player in players:
            has[player] = []
            for i in range(n_cards[player]):
                c = random.choice(to_d)
                to_d.remove(c)
                has[player].append(c)
                # print(player, counter)
            if counter == 0:
                filler = "n"
            else:
                filler = "?"
            maybes[player] = []
            for key, value in r.items():
                r[key][player] = filler
            counter += 1
        my_items = ""
        for my_card in has[players[0]]:
            set_has_item(players[0],my_card)
            my_items += my_card
    else:
        game = sys.argv[1]
        turn = sys.argv[2]
        print("Trying to load game %s at turn %s" % (game, turn))
        filename = log_prefix + game + "_" + turn
        data = json.load(open(filename))
        players = data['players']
        n_cards = data['n_cards']
        my_items = data['my_items']
        r = data['r']
        maybes = data['maybes']
        turn_counter = int(turn)
else:
    print("Starting... ")
    print("Enter player names, starting with your name, enter nothing when finished")
    players_selected = False
    players = []
    while not players_selected:
        player = input("Player's name: ")
        if player == "":
            players_selected = True
        else:
            if len(players) == 0:
                filler = "n"
            else:
                filler = "?"
            players.append(player)
            maybes[player] = []
            for key, value in r.items():
                r[key][player] = filler
    items_selected = False
    items = input("Enter %s's items: " % players[0])
    my_items = items
    n_cards = {players[0]: len(items)}
    for item in str(items):
        set_has_item(players[0],item)
    for player in players[1:]:
        n = input("How many cards does %s hold? " % player)
        n_cards[player] = int(n)
print("Okay. Let the game begin!")
while True:
    for player in players:
        # print("check cards")
        check_cards()
        # print("printtable")
        printtable()
        # print("printmaybes")
        printmaybes()
        if automated:
            perform_check()
        else:
            dump_json()
        turn_counter += 1
        print("It's %s's turn(%i)!" % (player, turn_counter))

        if automated:
            if player == players[0]:
                items = ""
                unknown, murder = get_card_lists()
                for group in groups:
                    status = False
                    for item in group:
                        if item in unknown and not status:
                            items += item
                            status = True
                    for item in group:
                        if item in my_items and not status:
                            items += item
                            status = True
                    for item in group:
                        if item in murder and not status:
                            items += item
                            status = True
                    if not status:
                        items += group[0]
                        status = True
                        print("found no better choice")
            print("Asking for", items)
        else:
            items = input("Which items are asked for? ")

        if not items == "":
            for answering_player in get_players_from_here(player):
                if answering_player == players[0] and not automated:
                    to_show = []
                    for item in items:
                        if item in my_items:
                            to_show.append(colored(things[item],'green'))
                    if to_show != []:
                        input("You can show " + " or ".join(to_show) + " [Enter]")
                        break
                    else:
                        input("You can't show anything. [Enter]")
                else:
                    pred = predict_answer(answering_player, items)
                    if pred == color_value("?"):
                        pred = ""
                    else:
                        pred = "[Prediction " + pred + "]"
                    if automated:
                        shows = "n"
                        for item in items:
                            # print(item, has[answering_player])
                            if item in has[answering_player]:
                                shows = "y"
                                shown_card = item
                        print(answering_player,shows)
                    else:
                        shows = input("Does %s show a card? [y/n/s/e]%s " % (answering_player,pred))
                    if shows == "y":
                        if player == players[0]:
                            if automated:
                                card = shown_card
                            else:
                                card = input("Which card is it? ")
                            set_has_item(answering_player,card)
                        else:
                            new_maybe = []
                            valid = True
                            for item in items:
                                if r[item][answering_player] == "y": #make sure that the player has no cards involved in the maybe
                                    valid = False
                                if item_status(item) == "unknown":
                                    if r[item][answering_player] == "?":
                                        new_maybe.append(item)
                            new_maybe = list(set(new_maybe))
                            if len(new_maybe) == 1 and valid:
                                set_has_item(answering_player, new_maybe[0])
                            elif len(new_maybe) > 1:
                                if not new_maybe in maybes[answering_player]: #make sure that maybe does not exist
                                    if valid:
                                        maybes[answering_player].append(new_maybe)
                        break
                    elif shows == "n":
                        for item in items:
                            set_does_not_have_item(answering_player,item)
                    elif shows == "e":
                        break
