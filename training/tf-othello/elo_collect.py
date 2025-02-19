import subprocess
import os
import re
import shutil
import math
import sys
from functools import cmp_to_key


def skip_credentials(process):
    for x in range(5):
        line=process.stdout.readline()

def wait_for_prompt(process):
    line=process.stdout.read(7)

def play(process, turn_player, move):
    process.stdin.write('play '+turn_player+' '+move+'\n')
    process.stdin.flush()
    opponent=''
    if turn_player=='black':
        opponent='white'
    else:
        opponent='black'
    process.stdin.write('genmove '+opponent+'\n')
    process.stdin.flush()
    line=process.stdout.readline()
    while not line.startswith('Leela:'):
        line=process.stdout.readline()
    new_move=''
    for i in range(len(line) - 1, -1, -1):
        if line[i]==' ':
            new_move=line[i+1:len(new_move)-1]
            # print(new_move)
            break
    wait_for_prompt(process)
    return new_move

def test_network(black_net, white_net, number_of_games):

    white_wins=0
    print(black_net)
    print(white_net)
    game=0

    while game<number_of_games:
        try:
            print(f'Iteration number {game}')
            black = subprocess.Popen(
                ['./leelaz', '-v', '100','-q', '-w', black_net],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            skip_credentials(black)

            white = subprocess.Popen(
                ['./leelaz', '-v', '100', '-q','-w', white_net],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            skip_credentials(white)

            turn_player='black'
            winner=''
            
            # Play first move (works differently than the others)
            wait_for_prompt(black)
            black.stdin.write('genmove '+turn_player+'\n')
            black.stdin.flush()
            move= black.stdout.readline()
            move=move[2:]
            wait_for_prompt(black)
            wait_for_prompt(white)
            pass_counter=0
            player=white
            opponent=black
            num_moves=1
            while True:
                
                new_move=play(player,turn_player,move)
                num_moves+=1
                # print("Played "+move+", now playing "+new_move)
                if turn_player=='black':
                    turn_player='white'
                else:
                    turn_player='black'

                assert((turn_player=='white' and player==white) or (turn_player=='black' and player==black))

                if "resign" in new_move:
                    if turn_player=='black':
                        winner='white'
                        white_wins+=1
                    else:
                        winner='black'
                    break

                if "pass" in new_move:
                    pass_counter+=1
                else:
                    pass_counter=0

                # Match not over, switch players and update move
                # print(f"Pass counter is:{pass_counter}")
                if pass_counter>=2:
                    # print("2 passes in a row, game over")
                    break

                move=new_move
                player, opponent = opponent, player

            if(winner==''):
                # print(f"Victory by double pass after {num_moves} moves")
                # print("No more moves available")
                black.stdin.write('final_score\n')
                black.stdin.flush()
                final_score_black= black.stdout.readline()

                white.stdin.write('final_score\n')
                white.stdin.flush()
                final_score_white= white.stdout.readline()
                winner='black'
                assert final_score_black==final_score_white
                if 'W' in final_score_black:
                    white_wins+=1
                    winner='white'

            print("Game over, winner: "+winner)
            print(f"White winrate: {(white_wins/(game+1))*100}%")
            white.stdin.write('quit\n')
            white.stdin.flush()
            black.stdin.write('quit\n')
            black.stdin.flush()
            game+=1
        except OSError as e:
            print(f"An error occured, rerunning iteration number {game}")
    return (white_wins/(number_of_games))*100

def add_files(file, filelist):
    # print(file)
    name= os.fsdecode(file)
    # print(name)
    if os.path.isdir(name):
        for f in os.listdir(file):
            add_files(os.path.join(file,f), filelist)
    else: 
        if '.txt' in name:
            filelist.append(name)

def str_number(str1):
    met_number=False
    index=-1

    for i in range(len(str1) - 1, -1, -1):
        if str1[i].isnumeric():
            met_number=True
        if not str1[i].isnumeric() and met_number:
            index=i
            break
    return int(str1[index+1:len(str1)-7])

def str_order(str1, str2):
    str1n= str_number(str1)
    str2n= str_number(str2)
    return str1n-str2n

def fname(str_path):
    begin = 0;
    for i in range(len(str_path) - 1, -1, -1):
        if str_path[i] == '/':
            begin = i + 1;
            break;
    return str_path[begin:];

retti_path="/media/heathcliff/epi/temp_gen1/"
filelist=[]
add_files(os.fsencode(retti_path), filelist)
# print(filelist)
key_func = cmp_to_key(str_order)
filelist.sort(key=key_func)
# print(filelist)

elo=24722.252358698926
n_games=400
print('#network, winrate, elo', file=sys.stderr)
print(fname(filelist[0])+f', {0}, {0}', file=sys.stderr)
for i in range(len(filelist)-1):
    black_net=filelist[i]
    white_net=filelist[i+1]
    white_wr= test_network(black_net,white_net, n_games)
    white_wrp= white_wr/100
    if white_wrp==1:
        elo+=n_games
    else:
        elo+= n_games*math.log10(white_wrp/(1-white_wrp))
    print(fname(white_net)+f', {white_wr}, {elo}', file=sys.stderr)



