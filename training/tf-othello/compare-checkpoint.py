import subprocess
import os
import re
import shutil
import csv
from functools import cmp_to_key
from config import *

def save_results(generation, opponent, winrate, result):
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

def test_network(black_net, white_net, number_of_games, b_or_w):

    print(f"Black player: {black_net}")
    print(f"White player: {white_net}")

    white_wins=0
    game=0

    while game<number_of_games:
        try:
            print(f'Iteration number {game}')
            black = subprocess.Popen(
                [leelaz, '-v', '150','-q','-w', black_net],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            skip_credentials(black)

            white = subprocess.Popen(
                [leelaz, '-v', '150','-q','-w', white_net],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            skip_credentials(white)

            turn_player='black'
            winner=''
            match_result=''

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
                        match_result='Black resigned'
                    else:
                        winner='black'
                        match_result='White resigned'
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
            command = f'printsgf b_or_w_checkpoint_{game}.sgf\n'
            white.stdin.write(command)
            white.stdin.flush()

            print("Game over, winner: "+winner)
            print(f"White winrate: {(white_wins/(game+1))*100}% after {num_moves} moves")
            white.stdin.write('quit\n')
            white.stdin.flush()
            black.stdin.write('quit\n')
            black.stdin.flush()
            white.wait()

            # Edits the SGF
            sgf_edit(f"b_or_w_checkpoint_{game}.sgf", num_moves, match_result)

            game+=1
        except OSError as e:
            print(f"An error occured, rerunning iteration number {game}")
            print(e)

    if b_or_w == 'b':
        return (white_wins/(number_of_games))*100
    else:
        return 100.0 - (white_wins/(number_of_games))*100

while True:
    num_gen = int(input("Checkpoint generation: "))
    if num_gen in [5, 25, 50, 75, 100, 125, 150, 175, 200, 225]:
        break
    print("Insert valid checkpoint generation")

while True:
    b_or_w = input("Checkpoint will play as b or w: ")
    if b_or_w in ['b', 'w']:
        break
    print("Insert valid character (b or w)")

results_file = f"{num_gen}gen_{b_or_w}.csv"
black_net = save_gen_dir + f"/{num_gen}/{num_gen}gen.txt"

# Cretes the sgf archives directory
os.makedirs(sgf_archive, exist_ok=True)
os.makedirs(compare_chkpt_sgf, exist_ok=True)

# Create the main directory for this generation's sgf files
gen_dir = f"{num_gen}gen_{b_or_w}"
gen_dir_path = compare_chkpt_sgf + f"/{gen_dir}"
os.makedirs(gen_dir_path, exist_ok=True)

max_gen = 275
gen_counter = 226

# Play 50 matches against everyone
while gen_counter <= max_gen:

    white_net = save_gen_dir + f"/{gen_counter}/{gen_counter}gen.txt"

    if b_or_w == 'b':
        winrate = test_network(black_net, white_net, 50, b_or_w)
    else:
        winrate = test_network(white_net, black_net, 50, b_or_w)

    # Save the results of the matches in the csv file
    result = f"{num_gen} wins" if winrate <= 55 else f"{num_gen} loses"
    save_results(f"{num_gen}gen", f"{gen_counter}gen", round(winrate,2), result)

    # print(f"100 games against {gen_counter}gen.\nFinal winrate:{winrate}")

    # Directory for this match
    save_path = f"{num_gen}gen_vs_{gen_counter}gen"
    # Make directory for this match
    os.makedirs(save_path, exist_ok=True)
    # Move the sgf into the directory
    os.system(f"mv b_or_w_checkpoint*.sgf {save_path}")
    # Move the match directory to the main directory
    os.system(f"mv {save_path} {gen_dir_path}")

    gen_counter += 1