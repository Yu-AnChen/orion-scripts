from subprocess import call
import time
import datetime

command = '''
python c:/Users/Public/Downloads/S3segmenter/large/S3segmenter.py
    --imagePath "{}"
    --stackProbPath "{}"
    --outputPath "{}"
    --area-max 50000 --expand-size 5 --maxima-footprint-size 7 --mean-intensity-min 128
'''

import pathlib
import csv

with open(r'C:\Users\Public\Downloads\orion-scripts\file_list.csv') as file_config_csv:
    csv_reader = csv.DictReader(file_config_csv)
    file_config = [dict(row) for row in csv_reader]

group_dir = pathlib.Path(r'C:\rcpnl\mcmicro')
ome_dir = pathlib.Path(r'C:\rcpnl\tissue')

for c in file_config[:]:
    o = ome_dir / c['path']
    n = c['name']

    print('Processing', n)
    prob_path = str(group_dir / n / 'unmicst2' / f'{n}_Probabilities_0.tif')
    out_path = str(group_dir / n / 'segmentation')
    command_final = command.format(
        str(o),
        prob_path,
        out_path
    )
    start_time = int(time.perf_counter())
    # print(command_final)
    call(' '.join(command_final.split()))
    end_time = int(time.perf_counter())

    print('elapsed', datetime.timedelta(seconds=end_time-start_time))
    print('')