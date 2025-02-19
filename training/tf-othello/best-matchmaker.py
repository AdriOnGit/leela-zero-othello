import subprocess
import os
import re
import shutil
import csv
from functools import cmp_to_key
from config import *

# Path to the best-network.txt
black_net_prefix = best_network

results_file = "best-matchmaker-results.csv"

def save_results(generation, opponent, games_played, winrate, result):
    file_exists = os.path.isfile(results_file)
    with open(results_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["generation", "opponent", "games_played", "winrate", "result"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "generation": generation,
            "opponent": opponent,
            "games_played": games_played,
            "winrate": opponent_winrate,
            "result": result
        })

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
                [leelaz, '-v', '100','-q','-w', black_net],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            skip_credentials(black)

            white = subprocess.Popen(
                [leelaz, '-v', '100','-q','-w', white_net],
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
                #print("Played "+move+", now playing "+new_move)
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

            # Prints the sgf file of the match
            command = f'printsgf {game}.sgf\n'
            white.stdin.write(command)
            white.stdin.flush()

            print("Game over, winner: "+winner)
            print(f"White winrate: {(white_wins/(game+1))*100}% after {num_moves} moves")
            white.stdin.write('quit\n')
            white.stdin.flush()
            black.stdin.write('quit\n')
            black.stdin.flush()
            

            #Skip network if it's already won or lost
            if (white_wins/(number_of_games))*100>=55 and game+1!=number_of_games:
                number_of_games=game+1
                print("White network has already reached threshold, skipping")
                break
            if ((game+1-white_wins)/(number_of_games))*100>=55 and game+1!=number_of_games:
                number_of_games=game+1
                print("White network can't reach threshold, skipping")
                break
            game+=1
        except OSError as e:
            print(f"An error occured, rerunning iteration number {game}")
            print(e)
    return (white_wins/(number_of_games))*100, game

def split_str(str1):
    met_number=False
    index=-1
    for i in range(len(str1) - 1, -1, -1):
        if str1[i].isnumeric():
            met_number=True
        if not str1[i].isnumeric() and met_number:
            index=i
            break
    return (str1[:index], int(str1[index+1:len(str1)-4]))

def str_sort(str1, str2):
    prefix_str1, number_str1 = split_str(str1)
    prefix_str2, number_str2 = split_str(str2)
    if number_str1<number_str2:
        return -1
    elif number_str1>number_str2:
        return 1
    if len(prefix_str1)<len(prefix_str2):
        return -1
    elif len(prefix_str1)>len(prefix_str2):
        return 1
    return 0

black_net= black_net_prefix+".txt"
# Ask for the path
while True:
    white_net = input("Inserire il path del network:")
    if not os.path.exists(white_net):
        print("Path non valido!")
        continue
    else:
        break

#ID of the current white network model
numero_re = re.search(r'\d+', white_net)
numerello = numero_re.group()

# Cretes the sgf archives directory
os.makedirs(sgf_archive, exist_ok=True)
os.makedirs(matchmaker_sgf, exist_ok=True)

# Create the main directory for this generation's sgf files
num_generations = len([f for f in os.listdir(save_gen_dir) if f[0].isdigit()]) + 1
gen_dir = f"{num_generations}gen"
gen_dir_path = matchmaker_sgf + f"/{gen_dir}"
os.makedirs(gen_dir_path, exist_ok=True)

# Play 400 matches against the best network
winrate, game = test_network(black_net, white_net, 400)
print(f"400 games against the current best network\nFinal winrate:{winrate}")

# Moves the sgf matches into archives
os.system(f"mv *.sgf {gen_dir_path}")
# Zips the directory
os.system(f"cd {matchmaker_sgf} && tar -czvf {gen_dir}.tar.gz {gen_dir}")
# Deletes the zip directory
os.system(f"rm -r {gen_dir_path}")

# Save the results of the matches in the csv file
result = "Best wins" if winrate >= 55 else "Best loses"
save_results(num_generations, numerello, f"{game}/400", round(winrate,2), result)