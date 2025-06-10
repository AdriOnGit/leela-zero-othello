# Config file to set paths and iteration numbers

#################################
##     SETTINGS TO CHANGE
#################################

# Number of iterations for auto-leela
games_per_generation = 2500

# Path to LZO - general directory
LZO = "/media/heathcliff/LZO"

#################################
#################################

# leela_files path
leela_files = LZO + "/leela_files"
# training scripts path
tf_othello = leela_files + "/leela-zero-othello/training/tf-othello"
# best-network weights path
network = leela_files + "/current_promoted/best-network.txt"
# general best-network files path
best_network = leela_files + "/current_promoted/best-network"
# leelaz program path
leelaz = LZO + "/leelaz"
# Training directory path
dirname = leela_files + "/Training"
# training archives path
archive_path = leela_files + "/archived_training"
# general white_networks directory path
white_networks = leela_files + "/white_networks" 
# white_networks files path
path = white_networks + "/leelaz-model"
# leelalogs path
leela_logs = leela_files + "/leelalogs"
# network archives path
save_gen_dir = leela_files + "/network_generations"

# sgf archives path
sgf_archive = leela_files + "/archived_sgf"
# auto_leela sgf archive
al_sgf = sgf_archive + "/auto_leela_sgf"
# autoplay sgf archive
ap_sgf = sgf_archive + "/autoplay_sgf"
# matchmaker sgf archive
matchmaker_sgf = sgf_archive + "/matchmaker_sgf"
# compare-checkpoint sgf archive
compare_chkpt_sgf = sgf_archive + "/comp_chkpt_sgf"
# edax sgf archive
edax_sgf = sgf_archive + "/edax_sgf"
# egaroucid sgf archive
egaroucid_sgf = sgf_archive + "/egaroucid_sgf"

# auto-leela path
auto_leela = tf_othello + "/auto-leela.py"
# parse path
parse = tf_othello + "/parse.py"
# autoplay-best path
autoplay_best = tf_othello + "/autoplay-best.py"
