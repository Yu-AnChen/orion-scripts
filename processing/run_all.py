import sys
import pathlib
import subprocess
import argparse
import configparser


FLOW = ('unmicst', 's3seg', 'quantification')


def main(argv=sys.argv):
    
    CURR = pathlib.Path(__file__).resolve().parent

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        metavar='init_config-csv',
        required=True
    )
    parser.add_argument(
        '-m',
        metavar='module-params',
        required=False,
        default=None
    )
    parsed_args = parser.parse_args(argv[1:])

    init_config = configparser.ConfigParser(allow_no_value=True)
    init_config_path = CURR / 'run_all.ini'
    init_config.read(init_config_path)

    custom_config_path = parsed_args.m
    if custom_config_path is None:
        custom_config_path = init_config_path

    start = init_config['Processes']['start-at']
    stop = init_config['Processes']['stop-at']

    custom_config = configparser.ConfigParser(allow_no_value=True)
    custom_config.read(custom_config_path)
    
    start = custom_config.get('Processes', 'start-at', fallback=start)
    stop = custom_config.get('Processes', 'stop-at', fallback=stop)
    
    try:
        idx_start = FLOW.index(start)
        idx_stop = FLOW.index(stop)
    except ValueError as e:
        print(e)
        msg = f"start-at and stop-at only accept one of {FLOW}"
        raise(ValueError(f"\n\n{msg}\n\n"))

    if idx_start > idx_stop:
        msg = f"Specified start-at is {start}, stop-at can only be one of {FLOW[idx_start:]}"
        raise(ValueError(f"\n\n{msg}\n\n"))

    STEPS = FLOW[idx_start:idx_stop+1]

    env_paths = [
        pathlib.Path(init_config['CONDA ENV PATH'][step]).expanduser()
        for step in STEPS
    ]

    for step, env_path in zip(STEPS, env_paths):
        assert env_path.exists(), (
            f"conda env ({env_path}) for {step} step does not exist"
            f" you may need to update {init_config_path}"
            f" or setup the required conda env"
        )
    
    script_paths = [
        CURR / f"command-{step}.py"
        for step in STEPS
    ]

    for step, env_path, script_path in zip(STEPS, env_paths, script_paths):
        subprocess.run([
            'conda', 'run', '--no-capture-output',
            '-p', env_path,
            'python', script_path,
            '-c', parsed_args.c,
            '-m', custom_config_path
        ])

    return 0


if __name__ == '__main__':
    # python /home/ychen/mcmicro/orion-scripts/processing/run_all.py -c /home/ychen/mcmicro/orion-scripts/file_list.csv
    sys.exit(main())