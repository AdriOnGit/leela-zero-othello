import subprocess
import os
import re
import shutil
from functools import cmp_to_key
from config import *

# Path to the best-network.txt
black_net_prefix = best_network
# Path to the white networks
directory = os.fsencode(white_networks)

results_file = "autoplay-best-results.csv"
gens_loss_file = "gen_loss.txt"

def save_results(generation. steps, network, opponent, games_played, winrate, result):
    file_exists = os.path.isfile(results_file)
    with open(results_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["generation", "steps", "network", "opponent", "games_played", "winrate", "result"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "generation": generation,
            "steps": steps,
            "network": network,
            "opponent": opponent,
            "games_played": games_played,
            "winrate": winrate,
            "result": result
        })

def save_gens_loss(gens_loss):
    with open(gens_loss_file, 'w') as f:
        f.write(str(gens_loss))

def load_gens_loss():
    with open(gens_loss_file, 'r') as f:
        return int(f.read())

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
            command = f'printsgf > {game}_ap.sgf\n'
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
white_networks=[]
regex = re.compile(r'^leelaz-model-(.)*\d+.txt$')
key_func = cmp_to_key(str_sort)
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if regex.match(filename):
        white_networks.append(filename)
white_networks.sort(key=key_func)

# best-network inside current_promoted
current_network = black_net

# networks that win against current_network
promoted_network = None

# Cretes the sgf archives directory
os.makedirs(sgf_archive, exist_ok=True)
os.makedirs(ap_sgf, exist_ok=True)

# Create the main directory for this generation's sgf files
num_generations = len([f for f in os.listdir(save_gen_dir) if f[0].isdigit()]) + 1
gen_dir = f"{num_generations}gen"
gen_dir_path = ap_sgf + f"/{gen_dir}"
os.makedirs(gen_dir_path, exist_ok=True)

step_counter = 0
for item in white_networks:
    # Counter of steps during Training
    step_counter += 1

    # Initialize white_net
    white_net = os.path.abspath(directory).decode('utf-8')+'/'+item

    #ID of the current white network model
    _,numerello=split_str(white_net)

    # If there is no best network play 400 matches against current
    if promoted_network == None:
        winrate = test_network(current_network, white_net, 400)
        print(f"400 games against the current best network\nFinal winrate:{winrate}")

        # Save the results of the matches in the csv file
        result = "Win + Promotion" if winrate >= 55 else "Loss"
        save_results(num_generations, numerello, 2000*step_counter, "best", f"{game}/400", round(winrate,2), result)

        # Creates the directory to zip for the sgf files 
        sgf_dir = f"best_vs_{numerello}_400"
        full_path = os.path.join(gen_dir_path, sgf_dir)
        os.makedirs(full_path, exist_ok=True)
        # Moves the matches into the new directory
        os.system(f"mv *.sgf {full_path}")
        # Zips the directory
        os.system(f"cd {ap_sgf} && tar -czvf {sgf_dir}.tar.gz {sgf_dir}")
        # Deletes the zip directory
        os.system(f"rm -r {full_path}")

        if winrate >= 55:
            promoted_network = white_net
            print(f"The new network has been promoted with a winrate of {winrate}")

    else: # If there is a best network play 200 matches against current and 200 against best
        current_vs_new_winrate = test_network(current_network, white_net, 200)
        print(f"200 games against the current best network.\nFinal winrate:{current_vs_new_winrate}")

        # Save the results of the matches in the csv file
        result = "Win" if current_vs_new_winrate >= 55 else "Loss"
        save_results(num_generations, numerello, 2000*step_counter, "best", f"{game}/200", round(current_vs_new_winrate, 2), result)
        
        # Creates the directory to zip for the sgf files 
        sgf_dir = f"best_vs_{numerello}_200"
        full_path = os.path.join(gen_dir_path, sgf_dir)
        os.makedirs(full_path, exist_ok=True)
        # Moves the matches into the new directory
        os.system(f"mv *.sgf {full_path}")
        # Zips the directory
        os.system(f"cd {ap_sgf} && tar -czvf {sgf_dir}.tar.gz {sgf_dir}")
        # Deletes the zip directory
        os.system(f"rm -r {full_path}")

        best_vs_new_winrate = test_network(promoted_network, white_net, 200)    
        print(f"200 games against the new best network.\nFinal winrate:{best_vs_new_winrate}")

        if best_vs_new_winrate >= 55 and current_vs_new_winrate >= 55:
            result = "Win + Promotion"
        elif best_vs_new_winrate >= 55 and current_vs_new_winrate < 55:
            result = "Win"
        else:
            result = "Loss"
        save_results(num_generations, numerello, 2000*step_counter, "promoted", f"{game}/200", round(best_vs_new_winrate,2), result)
        
        #ID of the current promoted network model
        _,promoted_num=split_str(promoted_network)

        # Creates the directory to zip for the sgf files 
        sgf_dir = f"{promoted_num}_vs_{numerello}_200"
        full_path = os.path.join(gen_dir_path, sgf_dir)
        os.makedirs(full_path, exist_ok=True)
        # Moves the matches into the new directory
        os.system(f"mv *.sgf {full_path}")
        # Zips the directory
        os.system(f"cd {ap_sgf} && tar -czvf {sgf_dir}.tar.gz {sgf_dir}")
        # Deletes the zip directory
        os.system(f"rm -r {full_path}")

        # The new network must have a winrate of at least 55% against both networks (current and best)
        if (current_vs_new_winrate >= 55 and best_vs_new_winrate >= 55):
            promoted_network = white_net
            print(f"The new network has been promoted since it had winrates of:")
            print(f"Current vs new: {current_vs_new_winrate}")
            print(f"Best vs new: {best_vs_new_winrate}")


gens_loss = load_gens_loss()

if promoted_network == None:
    if gens_loss == 5:
        
    promoted_network = black_net
    
print("The promoted network is "+promoted_network)

_,numerello=split_str(promoted_network)
save_prefix=(os.path.abspath(directory).decode('utf-8')+f"/leelaz-model-{numerello}")

if promoted_network!=black_net:
    count=1
    os.makedirs(save_gen_dir, exist_ok=True)
    shutil.copyfile(promoted_network, black_net)
    shutil.copyfile(save_prefix+".index", black_net_prefix+".index")
    shutil.copyfile(save_prefix+".meta", black_net_prefix+".meta")
    
    regex2= re.compile(rf'^leelaz-model-{numerello}.data*')
    datafile=''
    counter=0

    for file in os.listdir(directory):
        filename= os.fsdecode(file)
        if regex2.match(filename):
            counter+=1
            datafile=filename
    assert counter==1
    print(datafile)
    suffix=''
    for i in range(len(datafile)):
        if datafile[i]==".":
            suffix=datafile[i:]
            break
    assert(suffix!='')
    print(suffix)
    shutil.copyfile(save_prefix+suffix, black_net_prefix+suffix)
    
    for file in os.listdir(os.fsencode(save_gen_dir)):
        count+=1
    path = os.path.join(save_gen_dir, f"{count}")
    print(path)
    try:
        os.makedirs(path, exist_ok=True)
        print("Directory created successfully")
    except OSError as error:
        print(f"Error creating directory: {error}")
    shutil.copyfile(promoted_network, save_gen_dir+f"/{count}/{count}gen.txt")
    shutil.copyfile(save_prefix+".index", save_gen_dir+f"/{count}/{count}gen.index")
    shutil.copyfile(save_prefix+".meta", save_gen_dir+f"/{count}/{count}gen.meta")
    shutil.copyfile(save_prefix+suffix, save_gen_dir+f"/{count}/{count}gen"+suffix)




    