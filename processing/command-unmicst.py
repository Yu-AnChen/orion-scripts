import argparse
import datetime
import pathlib
import sys
import time

import run_all_utils
from module_scripts import unmicst_predict_once as unmicst


MODULE_NAME = 'unmicst'
ORION_DEFAULTS = [
    ('nucleus_channel', 1, 'int'),
    ('size_scaling_factor', 0.5, 'float'),
    ('intensity_min', 400, 'float'),
    ('intensity_max', 8000, 'float'),
    ('intensity_gamma', 0.8, 'float'),
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
    # Go from 1-based indexing to 0-based indexing
    module_params['nucleus_channel'] -= 1

    for config in file_config[:]:
        config = run_all_utils.set_config_defaults(config)

        img_path = config['path']

        name = config['name']
        out_dir = config['out_dir']
        nucleus_channel = module_params['nucleus_channel']
        output_path = out_dir / name / 'unmicst2' / f'{name}_Probabilities_{nucleus_channel}.ome.tif'
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        
        print('Processing', name)
        start_time = int(time.perf_counter())
        unmicst.process_slide(
            img_path=img_path,
            output_path=output_path,
            **module_params
        )
        end_time = int(time.perf_counter())

        print('elapsed', datetime.timedelta(seconds=end_time-start_time))
        print()

        run_all_utils.to_log(
            log_path, img_path, end_time-start_time, module_params
        )

    return 0


if __name__ == '__main__':
    sys.exit(main())