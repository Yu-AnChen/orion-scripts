import argparse
import datetime
import os
import pathlib
import subprocess
import sys
import time

import psutil
import run_all_utils
from joblib import Parallel, delayed

command = '''
python ../modules/quantification/CommandSingleCellExtraction.py
    --masks {}
    --image "{}" 
    --output "{}"
    --channel_names "{}"
'''

MODULE_NAME = 'quantification'
ORION_DEFAULTS = [
    ('masks name pattern', '*cellRing*.ome.tif', ''),
    ('channel_names', None, '')
]


def estimate_RAM_usage(img_path, num_masks):
    import tifffile
    img_path = pathlib.Path(img_path)
    with tifffile.TiffFile(img_path) as tif:
        shape = tif.series[0].shape
    shape = sorted(shape)[-2:]
    ram_base = (shape[0] * shape[1] / 1024**2) / 1000
    return (1+2+4*num_masks) * ram_base


def main(argv=sys.argv):

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        metavar='config-csv',
        required=True
    )
    parser.add_argument(
        '-m',
        metavar='module-params',
        required=False,
        default=None
    )
    parsed_args = parser.parse_args(argv[1:])
    
    CURR = pathlib.Path(__file__).resolve().parent

    file_config, module_params, log_path = run_all_utils.init_run(
        parsed_args, ORION_DEFAULTS, MODULE_NAME
    )

    assert module_params['channel_names'] is not None, 'channel_names is required'
    marker_csv_path = pathlib.Path(module_params['channel_names'])
    assert marker_csv_path.exists(), f"{marker_csv_path} does not exist"

    commands = []
    quant_out_dirs = []
    ram_usages = []
    for config in file_config[:]:
        config = run_all_utils.set_config_defaults(config)

        name = config['name']
        out_dir = config['out_dir']

        masks = module_params['masks name pattern'].split(',')
        img_path = pathlib.Path(config['path'])
        img_stem = img_path.name.split('.')[0]
        mask_dir = out_dir / name / 'segmentation' / img_stem
        try:
            mask_paths = [sorted(mask_dir.glob(m))[0] for m in masks]
        except IndexError as e:
            print(f"\nError: {mask_dir} does not contain file with name pattern {masks}\n")
            raise(e)
        
        quant_out_dir = out_dir / name / 'quantification'
        quant_out_dir.mkdir(exist_ok=True, parents=True)

        command_run = [
            'python',
            CURR.parent / 'modules/quantification/CommandSingleCellExtraction.py',
            '--image', config['path'],
            '--output', quant_out_dir,
            '--masks',
        ]
        command_run.extend(mask_paths)
        for kk, vv in module_params.items():
            if ' ' not in kk:
                command_run.extend([f"--{kk}", str(vv)])

        commands.append(command_run)
        quant_out_dirs.append(quant_out_dir)
        ram_usages.append(estimate_RAM_usage(config['path'], len(mask_paths)))

    def run(cmd, out_dir):
        name = out_dir.parent.name
        print('Start processing', name)

        start_time = int(time.perf_counter())
        with open(out_dir / 'quant.log', 'a') as f:
            f.write(f"{datetime.datetime.now()}\n")
        with open(out_dir / 'quant.log', 'a') as f:
            subprocess.run(cmd, stdout=f)
        end_time = int(time.perf_counter())

        print('Finished', name, '- time used', datetime.timedelta(seconds=end_time-start_time))
        print()

        run_all_utils.to_log(
            log_path, config['path'], end_time-start_time, module_params
        )
    
    available_ram = psutil.virtual_memory().available / 1024**3
    n_jobs_max = int(available_ram // max(ram_usages))
    n_cpus = os.cpu_count()
    n_jobs = min(n_jobs_max, n_cpus, len(file_config))
    
    Parallel(n_jobs=n_jobs, backend='loky', verbose=1)(
        delayed(run)(cmd, dir) for cmd, dir in zip(commands, quant_out_dirs)
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())