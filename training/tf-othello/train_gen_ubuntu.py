import os
import subprocess
import shutil
from config import *

# Number of iterations for the script
num_iterations=5

for i in range(num_iterations):
	shutil.rmtree(white_networks, ignore_errors=True)
	os.makedirs(white_networks, exist_ok=True)

	# Run auto-leela
	subprocess.run(['python', auto_leela])

	# Check if this is first generation, then run parse.py accordingly
	num_generations = len([f for f in os.listdir(save_gen_dir) if f[0].isdigit()])
	if (num_generations == 0):
		subprocess.run(['python', parse, '10','128', os.path.join(dirname, "/tmp")])
	else:
		subprocess.run(['python', parse, '10','128', os.path.join(dirname, "/tmp"), best_network])

	# Run autoplay-best
	subprocess.run(['python', autoplay_best])
