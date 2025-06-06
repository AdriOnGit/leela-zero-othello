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
directory = os.fsencode(dirname)
max = 0

# Cretes the sgf archives directory
os.makedirs(sgf_archive, exist_ok=True)
os.makedirs(al_sgf, exist_ok=True)

for file in os.listdir(directory):
    filename= os.fsdecode(file)
    begin=-1
    end=-1
    for char_n in range(len(filename)):
        if filename[char_n].isnumeric() and begin==-1:
            begin=char_n
        if begin!=-1 and not filename[char_n].isnumeric():
            end=char_n
            break
    assert begin!=-1 and end!=-1
    current_number=int(filename[begin:end])
    # print(f"{current_number} "+filename)
    if current_number > max:
        max=current_number
max+=1

for i in range(max, max+num_iterations):
    # Start the subprocess
    print(f'Running iteration number {i}')
    p = subprocess.Popen(
        [leelaz, '-v', '150', '-r5', '--noponder', '-q', '-m10', '-n', '-w', network],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
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

    # Send the dump_training command
    command = f'dump_training {winner} tmp{i}\n'
    #print(command)
    p.stdin.write(command)
    p.stdin.flush()

    # Prints the sgf file of the match
    command = f'printsgf {i}_al.sgf\n'
    p.stdin.write(command)
    p.stdin.flush()

    # Quit Leela Zero
    p.stdin.write('quit\n')
    p.stdin.flush()

    # Edits the SGF
    sgf_edit(f"{i}_al.sgf", num_moves)

time.sleep(10)

# Copies the matches in Training
os.system(f"cp tmp* {dirname}")
# Creates the directory to zip for the matches
matches_dir = f"{(max + num_iterations - 1)}_iter"
full_path = os.path.join(archive_path, matches_dir)
os.makedirs(full_path, exist_ok=True)
# Moves the matches into the new directory
os.system(f"mv tmp* {full_path}")
# Zips the directory
os.system(f"cd {archive_path} && tar -czf {matches_dir}.tar.gz {matches_dir}")
# Deletes the zip directory
os.system(f"rm -r {full_path}")

# Creates the directory to zip for the sgf files 
sgf_dir = f"{(max+num_iterations - 1)}_al_sgf"
full_path = os.path.join(al_sgf, sgf_dir)
os.makedirs(full_path, exist_ok=True)
# Moves the matches into the new directory
os.system(f"mv *.sgf {full_path}")
# Zips the directory
os.system(f"cd {al_sgf} && tar -czf {sgf_dir}.tar.gz {sgf_dir}")
# Deletes the zip directory
os.system(f"rm -r {full_path}")


if(max>=12500):
    for i in range(max-12500,max-10000):
       os.unlink(dirname+f"/tmp{i}.0.gz") 

print("Finished")
