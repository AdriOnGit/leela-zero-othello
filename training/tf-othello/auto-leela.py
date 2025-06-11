import subprocess
import os
import time
from config import *

def wait_for_prompt(process):
    line=process.stdout.read(7)
def skip_credentials(process):
    for x in range(5):
        line=process.stdout.readline()

def sgf_edit(sgf, num_moves):
    # Read the content of the SGF file
    with open(sgf, 'r') as file:
        sgf_content = file.read()

    # Replace 'GM[1]' with 'GM[2]' for Othello
    updated_sgf_content = sgf_content.replace('GM[1]', 'GM[2]')

    # Append a comment with match result and moves number
    comment = f'Match ended with {num_moves} moves.'
    updated_sgf_content += f"\n(;C[{comment}])"  # Append the comment as a new node

    # Write the updated content back to the same file
    with open(sgf, 'w') as file:
        file.write(updated_sgf_content)

def play(process, turn_player):

    process.stdin.write('genmove '+turn_player+'\n')
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
    return new_move

# Creates the leela_files directory
os.makedirs(leela_files, exist_ok=True)

# Creates the Training directory
os.makedirs(dirname, exist_ok=True)

# Creates the sgf archives directory
os.makedirs(sgf_archive, exist_ok=True)
os.makedirs(al_sgf, exist_ok=True)

# Collect list of files both in Training and in running directory
dirlist = os.listdir(dirname) + os.listdir(".")

# Select dump_training files of format tmp1234.0.gz, get the number and make a list
# Add 0 to deal with empty directory at the beginning
nums = [0] + [int(x.replace("tmp", "").replace(".0.gz", "")) for x in dirlist if x.endswith(".0.gz")]

max_num = max(nums)
print(f"Current number of games {max_num}.")

current_gen   = max_num // games_per_generation
missing_games = -max_num % games_per_generation
games_to_play = missing_games or games_per_generation
target_games  = max_num + games_to_play

print(f"Starting {games_to_play} games for generation {current_gen+1}.")
game_indices  = range(max_num+1, target_games+1)

for i in game_indices:
    # Start the subprocess
    print(f'Running game number {i}')
    p = subprocess.Popen(
        [leelaz, '-w', network] + leelaz_args,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        bufsize=1,
        text=True
    )
    skip_credentials(p)

    turn_player='black'
    winner=''
    pass_counter=0
    num_moves=0
    
    while True:
        new_move=play(p,turn_player)
        #print("Played "+new_move+" for "+turn_player)
        num_moves+=1
        #print(new_move)

        if "resign" in new_move:
            #print("Played "+new_move+" for "+turn_player)
            if turn_player=='black':
                winner='w'
            else:
                winner='b'
            break

        if "pass" in new_move:
            pass_counter+=1
        else:
            pass_counter=0

        # Match not over, switch players and update move
        #print(f"Pass counter is:{pass_counter}")
        if pass_counter>=2:
            #print("2 passes in a row, game over)__________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________")
            break

        if turn_player=='black':
            turn_player='white'
        else:
            turn_player='black'

    # p.stdin.write('auto\n')
    # p.stdin.flush()
    wait_for_prompt(p)
    p.stdin.write('final_score\n')
    p.stdin.flush()
    final_score= p.stdout.readline()
    #print("Final score is "+final_score)
    if(winner==''):
        print(f"Victory by double pass after {num_moves} moves")
        print(final_score)
        winner='b'
        if 'W' in final_score:
            winner='w'
    # p.stdin.write('final_score\n')
    # p.stdin.flush()


    # line = ''
    # while True:
    #     line = p.stdout.readline()
    #     if line.startswith('Leela:'):
    #         break

    # # Determine the winner
    # winner = line[16].lower()
    print("Winner: "+ (winner))
    assert winner == 'w' or winner == 'b'

    # Prints the sgf file of the match
    command = f'printsgf {i}_al.sgf\n'
    p.stdin.write(command)
    p.stdin.flush()

    # Send the dump_training command
    command = f'dump_training {winner} tmp{i}\n'
    #print(command)
    p.stdin.write(command)
    p.stdin.flush()

    # Quit Leela Zero
    p.stdin.write('quit\n')
    p.stdin.flush()

    time.sleep(0.5)

    # Edits the SGF
    sgf_edit(f"{i}_al.sgf", num_moves)

time.sleep(2)

# Copies the matches in Training
os.system(f"cp tmp* {dirname}")
# Creates the directory to zip for the matches
matches_dir = f"{(max_num + games_per_generation - 1)}_iter"
full_path = os.path.join(archive_path, matches_dir)
os.makedirs(full_path, exist_ok=True)
# Moves the matches into the new directory
os.system(f"mv tmp* {full_path}")
# Zips the directory
os.system(f"cd {archive_path} && tar -czf {matches_dir}.tar.gz {matches_dir}")
# Deletes the zip directory
os.system(f"rm -r {full_path}")

# Creates the directory to zip for the sgf files 
sgf_dir = f"{(max_num + games_per_generation - 1)}_al_sgf"
full_path = os.path.join(al_sgf, sgf_dir)
os.makedirs(full_path, exist_ok=True)
# Moves the matches into the new directory
os.system(f"mv *.sgf {full_path}")
# Zips the directory
os.system(f"cd {al_sgf} && tar -czf {sgf_dir}.tar.gz {sgf_dir}")
# Deletes the zip directory
os.system(f"rm -r {full_path}")

out_of_window = target_games - games_per_generation * training_window
if(out_of_window > 0):
    for s in os.listdir(dirname):
        if s.endswith(".0.gz"):
            if int(s.replace("tmp", "").replace(".0.gz", "")) <= out_of_window:
                os.unlink(os.path.join(dirname, s))

print("Finished")
