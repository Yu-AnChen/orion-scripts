import argparse
import datetime
import pathlib
import subprocess
import sys
import time

import run_all_utils


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
    for config in file_config[:]:
        config = run_all_utils.set_config_defaults(config)

        name = config['name']
        out_dir = config['out_dir']

        print('Processing', name)

        masks = module_params['masks name pattern'].split(',')
        img_path = pathlib.Path(config['path'])
        img_stem = img_path.name.split('.')[0]
        mask_dir = out_dir / name / 'segmentation' / img_stem
        try:
            mask_paths = [sorted(mask_dir.glob(m))[0] for m in masks]
        except IndexError as e:
            print(f"\nError: {mask_dir} does not contain file with name pattern {masks}\n")
            raise(e)
        mask_paths = [f'"{p}"' for p in mask_paths]

        command_run = [
            'python',
            CURR.parent / 'modules/quantification/CommandSingleCellExtraction.py',
            '--image', config['path'],
            '--output', out_dir / name / 'quantification',
            '--masks',
        ]
        command_run.extend(mask_paths)
        for kk, vv in module_params.items():
            if ' ' not in kk:
                command_run.extend([f"--{kk}", str(vv)])

        commands.append(command_run)
        # start_time = int(time.perf_counter())
        # subprocess.run(command_run)
        # end_time = int(time.perf_counter())

        # print('elapsed', datetime.timedelta(seconds=end_time-start_time))
        # print()

        # run_all_utils.to_log(
        #     log_path, config['path'], end_time-start_time, module_params
        # )

    return 0


if __name__ == '__main__':
    sys.exit(main())