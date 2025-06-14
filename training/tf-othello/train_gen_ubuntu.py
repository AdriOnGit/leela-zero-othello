import os
import subprocess
import time
from config import *

while True:
	# Run auto-leela
        subprocess.run(['python', auto_leela])

        curr_gen = int(max(os.listdir(save_gen_dir), key=int))
        curr_gen_dir = os.path.join(save_gen_dir, str(curr_gen))
        last_model = [s for s in os.listdir(curr_gen_dir)
                      if s.endswith("meta")][0].replace(".meta", "")
        
        parse_args = ["--blocks", str(blocks),
                      "--filters", str(filters),
                      "--train", os.path.join(dirname, ""),
                      "--test", os.path.join(test_dir, ""),
                      "--restore", os.path.join(curr_gen_dir, last_model)]
        subprocess.run(['python', parse] + parse_args)

        os.system(f"gzip {white_networks}/leelaz-model-*.txt")
        os.system(f"cp {white_networks}/leelaz-model-*.txt.gz {best_network}")
        new_gen_dir = os.path.join(save_gen_dir, str(curr_gen+1))
        os.makedirs(new_gen_dir)
        os.system(f"mv {white_networks}/* {new_gen_dir}")

        print(f"Network for generation {curr_gen+1} is ready. Starting self-plays in 10 seconds.")
        time.sleep(10)
