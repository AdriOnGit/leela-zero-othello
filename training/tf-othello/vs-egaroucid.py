import subprocess
import os
import sys
import csv
from config import *

egaroucid= '/media/heathcliff/LZO/Egaroucid-console_v7.5.1/bin/Egaroucid_for_Console.out'
network='/media/heathcliff/LZO/leela_files/network_generations/150/150gen.txt'

def save_results(results_file, generation, opponent, winrate, result):
    file_exists = os.path.isfile(results_file)
    with open(results_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["generation", "opponent", "winrate", "result"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "generation": generation,
            "opponent": opponent,
            "winrate": winrate,
            "result": result
        })

def sgf_edit(sgf, num_moves, match_result):
    # Read the content of the SGF file
    with open(sgf, 'r') as file:
        sgf_content = file.read()

    # Replace 'GM[1]' with 'GM[2]' for Othello
    updated_sgf_content = sgf_content.replace('GM[1]', 'GM[2]')

    # Replace [tt] with [] for pass
    updated_sgf_content = updated_sgf_content.replace('[tt]', '[]')

    # Append a comment with match result and moves number
    comment = f'Match ended with {num_moves} moves with {match_result}.'
    updated_sgf_content += f"\n(;C[{comment}])"  # Append the comment as a new node

    # Write the updated content back to the same file
    with open(sgf, 'w') as file:
        file.write(updated_sgf_content)

def skip_credentials(process):
    for x in range(5):
        line=process.stdout.readline()

def wait_for_prompt(process):
    line=process.stdout.read(7)

def go_egaroucid(process, move, first=False):
    if first == True:
        process.stdin.write('go\n')
        process.stdin.flush()
        line=process.stdout.readline().strip()
        move_only = line.lstrip('> ').strip()
        # print(move_only)
        return move_only
    else:
        process.stdin.write('play '+move+'\n')
        process.stdin.flush()
        # line=process.stdout.readline()
        process.stdin.write('go\n')
        process.stdin.flush()
        line=process.stdout.readline().strip()
        # print('Egaroucid before line strip'+line)
        move_only = line.lstrip('> ').strip()
        # if 'over' in line:
        #     return 'F'
        #print(move_only)
        return move_only

def go_leela_b(process, move):
    if move is not None:
        process.stdin.write('play white '+move+'\n')
        process.stdin.flush()

    wait_for_prompt(process)
    process.stdin.write('genmove black\n')
    process.stdin.flush()

    line=process.stdout.readline().strip()
    line = line.replace('>', '').replace('=', '').strip()
    new_move=line.split()[-1]
    # new_move=''
    # for i in range(len(line) - 1, -1, -1):
    #     if line[i]==' ':
    #         new_move=line[i+1:len(new_move)-1]
    #         # print(new_move)
    #         break
    # print(new_move)
    wait_for_prompt(process)
    return new_move

def go_leela_w(process, move):
    # print('play black '+move+'\n')
    process.stdin.write('play black '+move+'\n')
    process.stdin.flush()
    wait_for_prompt(process)
    process.stdin.write('genmove white\n')
    process.stdin.flush()

    line=process.stdout.readline().strip()
    #print(line)
    line = line.replace('>', '').replace('=', '').strip()
    new_move=line.split()[-1]
    # line=process.stdout.readline()
    # new_move=''
    # for i in range(len(line) - 1, -1, -1):
    #     if line[i]==' ':
    #         new_move=line[i+1:len(new_move)-1]
    #         # print(new_move)
    #         break
    # print(new_move)
    wait_for_prompt(process)
    return new_move

def get_winner(process):
    process.stdin.write('final_score\n')
    process.stdin.flush()
    final_score= process.stdout.readline()
    # print(final_score)
    assert 'W' in final_score or 'B' in final_score
    if 'W' in final_score:
        return 'white'
    elif 'B' in final_score:
        return 'black'

def convert_move(move):
    # print(move)
    if move=='pass':
        return 'pass'
    if move=='ps':
        return 'pass'
    # print("Move is "+move)
    if move=='??':
        return '??'
    assert len(move)==2
    num= int(move[1])
    assert num>=1 and num<=8
    reflection_map = {
        1: 8,
        2: 7,
        3: 6,
        4: 5,
        5: 4,
        6: 3,
        7: 2,
        8: 1
    }

    # Return the reflected number from the map
    value =reflection_map.get(num, "Invalid input")
    # print("Move is "+move[0]+f"{value}")
    return (move[0]+f"{value}")

def test_network(number_of_games, visits, depth, leelaz_b_or_w):

    leelaz_wins=0
    game=0

    results_file= f"leelaz_{leelaz_b_or_w}_vs_{depth}egaroucid.csv"

    print(f'Running Leela with {visits} visits')
    print(f'Running Egaroucid with {depth} depth\n')

    while game<number_of_games:
        try:
            print(f'Iteration number {game}\n')

            # Leelaz first
            if leelaz_b_or_w == 'b':
                black = subprocess.Popen(
                    [leelaz, '-v',  f'{visits}', '-q', '-r', '0', '-w', network, '--randomvisits', '0', '--randomtemp', '0'],
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True
                )
                skip_credentials(black)

                white = subprocess.Popen(
                    [egaroucid,'-q','-l',f'{depth}'],
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True
                )

                # Leelaz plays first move
                move= convert_move(go_leela_b(black, None))
                num_moves= 1
                # print(f'{num_moves} Leelaz:'+move)

                while True:
                    move= convert_move(go_egaroucid(white, move))
                    if move=='??':
                        break
                    num_moves+=1
                    # print(f'{num_moves} Egaroucid:'+move)
                    new_move= go_leela_b(black, move)
                    # print('Leelaz:'+new_move)
                    num_moves+=1
                    move= convert_move(new_move)
                    # print(f'{num_moves} Leelaz:'+move)

                winner = get_winner(black)
                if(winner=='black'):
                    result= 'Leelaz wins'
                    leelaz_wins+=1
                else:
                    result= 'Leelaz loses'

                black.stdin.flush()
                black.stdin.write(f'printsgf {game}_egaroucid.sgf\n')
                black.stdin.flush()
                black.stdin.write('quit\n')
                black.stdin.flush()
                white.stdin.flush()
                white.stdin.write('quit\n')
                white.stdin.flush()
                black.wait()

                wr = (leelaz_wins/(game+1))*100
                save_results(results_file, game+1, depth, wr, result)
                print("Game over, winner: "+winner+f" with {num_moves} moves")
                print(f"Leelaz winrate: {wr}%")

                # Edits the SGF
                sgf_edit(f"{game}_egaroucid.sgf", num_moves, result)

                game+=1

            # Egaroucid first
            else:
                black = subprocess.Popen(
                    [egaroucid,'-q','-l',f'{depth}'],
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True
                )
                white = subprocess.Popen(
                    [leelaz, '-v',  f'{visits}','-q', '-r', '0', '-w',network,'--randomvisits','0', '--randomtemp','0'],
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True
                )
                skip_credentials(white)

                move= convert_move(go_egaroucid(black, None, True))
                # print(move)
                wait_for_prompt(white)
                num_moves=1

                while True:
                    move=convert_move(go_leela_w(white, move))
                    # print('Leela:'+move)
                    num_moves+=1
                    new_move=go_egaroucid(black,move)
                    # print('Egaroucid:'+new_move)
                    if new_move=='??':
                        break
                    num_moves+=1
                    move = convert_move(new_move)
                    # print('Egaroucid converted:'+move)

                winner=get_winner(white)
                if(winner=='white'):
                    result= 'Leelaz wins'
                    leelaz_wins+=1
                else:
                    result= 'Leelaz loses'

                white.stdin.flush()
                white.stdin.write(f'printsgf {game}_egaroucid.sgf\n')
                white.stdin.flush()
                white.stdin.write('quit\n')
                white.stdin.flush()
                black.stdin.write('quit\n')
                black.stdin.flush()
                white.wait()

                wr= (leelaz_wins/(game+1))*100
                save_results(results_file, game+1, depth, wr, result)
                print("Game over, winner: "+winner+f" with {num_moves} moves")
                print(f"Leelaz winrate: {wr}%")

                # Edits the SGF
                sgf_edit(f"{game}_egaroucid.sgf", num_moves, result)

                game+=1

        except Exception as e:
            print(f"An error occured, rerunning iteration number {game}")

    return (leelaz_wins/(number_of_games))*100

# Cretes the sgf archives directory
os.makedirs(sgf_archive, exist_ok=True)
os.makedirs(egaroucid_sgf, exist_ok=True)

b_or_w = ''
while True:
    b_or_w = input("Leelaz will play as b or w: ")
    if b_or_w in ['b', 'w']:
        break
    print("Insert valid character (b or w)")

winrate_file=f'total_winrate_{b_or_w}_egaroucid.csv'
number_of_games=200
visits= [10000]
depth= [4,5,7,8,9,11,13,15]
print('leelaz_visits,  egaroucid_depth, leelaz_winrate', file=sys.stderr)
sys.stderr.flush()
for nvis in visits:
    for ndep in depth:

        leela_winrate= test_network(number_of_games, nvis, ndep, b_or_w)
        result= "Leelaz wins" if leela_winrate >= 55 else "Leelaz loses"
        save_results(winrate_file, f"Leelaz {b_or_w}", ndep, leela_winrate, result)

        # Create the main directory for this depth's sgf files
        save_path = f"{b_or_w}_vs_{ndep}"
        # Make directory for this match
        os.makedirs(save_path, exist_ok=True)
        # Move the sgf into the directory
        os.system(f"mv *_egaroucid.sgf {save_path}")
        # Move the match directory to the main directory
        os.system(f"mv {save_path} {egaroucid_sgf}")

        print(f'{nvis},  {ndep}, {leela_winrate}', file=sys.stderr)
        sys.stderr.flush()

os.makedirs("./egaroucid_csv_files", exist_ok=True)
os.system(f"mv *egaroucid.csv egaroucid_csv_files")