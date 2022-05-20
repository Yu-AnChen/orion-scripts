import sys
sys.path.append(r'C:\Users\Public\Downloads\quantification')

import os
import pathlib
import datetime
import time

def main(slide_dir, ome_tiff_path, marker_csv_path):

    target_dir = slide_dir
    target_dir = pathlib.Path(target_dir)

    masks = [
        'cell.ome.tif',
        # 'nuclei.ome.tif'
    ]

    mask_paths = [
        sorted((target_dir / 'segmentation').rglob(f"{m}*"))[0]
        for m in masks
    ]

    import pipeline
    # import pyimagej_rolling_ball
    
    # p = pipeline.Pipeline(
    #     mask_paths=mask_paths,
    #     output_dir=target_dir / 'quantification' / 'ij_rb_100',
    #     img_path=ome_tiff_path,
    #     marker_csv_path=marker_csv_path,
    #     img_preprocess_func=pyimagej_rolling_ball.ij_rolling_ball_dask,
    #     img_preprocess_kwargs=dict(radius=100, verbose=False),
    #     table_prefix='ij_rb_100-',
    #     save_RAM=False
    # )

    q = pipeline.Pipeline(
        mask_paths=mask_paths,
        output_dir=target_dir / 'quantification' / 'raw',
        img_path=ome_tiff_path,
        marker_csv_path=marker_csv_path,
        img_preprocess_func=None,
        img_preprocess_kwargs=None,
        table_prefix='',
        save_RAM=False,
        skip=None
    )

    start_time = int(time.perf_counter())
    print(datetime.datetime.now(), '\n')

    # p.run()
    q.run()

    end_time = int(time.perf_counter())
    print('elapsed', datetime.timedelta(seconds=end_time-start_time))
    print('')


import pathlib
import csv

with open(r'C:\Users\Public\Downloads\orion-scripts\file_list.csv') as file_config_csv:
    csv_reader = csv.DictReader(file_config_csv)
    file_config = [dict(row) for row in csv_reader]

group_dir = pathlib.Path(r'C:\rcpnl\mcmicro')
ome_dir = pathlib.Path(r'C:\rcpnl\tissue')

marker_csv_path = r'C:\Users\Public\Downloads\orion-scripts\markers.csv'

names = [c['name'] for c in file_config]
slide_dirs = [
    group_dir / n 
    for n in names
]

ome_tiffs = [
    ome_dir / c['path']
    for c in file_config
]


for s, o in zip(slide_dirs[:], ome_tiffs[:]):
    print(slide_dirs)
    print(ome_tiffs)
    print('Processing', s.name)
    main(str(s), str(o), marker_csv_path)
    print()