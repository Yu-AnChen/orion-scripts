import argparse
import datetime
import pathlib
import subprocess
import sys
import time

import run_all_utils


command = '''
python ../modules/S3segmenter/large/S3segmenter.py
    --imagePath "{}"
    --stackProbPath "{}"
    --outputPath "{}"
    --probMapChan {probMapChan}
    --area-max 50000
    --expand-size {expand_size}
    --maxima-footprint-size {maxima_footprint_size}
    --mean-intensity-min {mean_intensity_min}
    --pixelSize {pixelSize}
'''


MODULE_NAME = 's3seg'
ORION_DEFAULTS = [
    ('probMapChan', 1, 'int'),
    ('expand-size', 5, 'int'),
    ('maxima-footprint-size', 13, 'int'),
    ('mean-intensity-min', 128, 'float'),
    ('pixelSize', 0.325, 'float'),
]


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

    for config in file_config[:]:
        config = run_all_utils.set_config_defaults(config)

        name = config['name']
        out_dir = config['out_dir']

        print('Processing', name)
        nucleus_channel = module_params['probMapChan'] - 1
        pmap_path = out_dir / name / 'unmicst2' / f'{name}_Probabilities_{nucleus_channel}.ome.tif'
        command_run = [
            'python',
            CURR.parent / 'modules/S3segmenter/large/S3segmenter.py',
            '--imagePath', config['path'],
            '--stackProbPath', pmap_path,
            '--outputPath', out_dir / name / 'segmentation',
            '--area-max', str(50000)
        ]
        for kk, vv in module_params.items():
            command_run.extend([f"--{kk}", str(vv)])
        
        print(command_run)
        start_time = int(time.perf_counter())
        # print(command_final)
        subprocess.run(command_run)
        end_time = int(time.perf_counter())

        print('elapsed', datetime.timedelta(seconds=end_time-start_time))
        print()

        run_all_utils.to_log(
            log_path, config['path'], end_time-start_time, module_params
        )

    return 0


if __name__ == '__main__':
    sys.exit(main())