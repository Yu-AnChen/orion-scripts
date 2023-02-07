import sys
import pathlib
import subprocess
import argparse
import configparser


def main(argv=sys.argv):
    
    CURR = pathlib.Path(__file__).resolve().parent

    config = configparser.ConfigParser()
    config.read(CURR / 'run_all.ini')

    unmicst_env_path = pathlib.Path(config['CONDA ENV PATH']['unmicst'])
    s3seg_env_path = pathlib.Path(config['CONDA ENV PATH']['s3seg'])
    for pp in [unmicst_env_path, s3seg_env_path]:
        assert pp.exists(), (
            f"conda env {pp} does not exist"
            f" you may need to update {CURR / 'run_all.ini'}"
        )

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


    unmicst = CURR / 'command-unmicst.py'
    s3seg = CURR / 'command-s3seg.py'
    quant = CURR / 'command-quant.py'


    subprocess.run([
        'conda', 'run', '--no-capture-output',
        '-p', unmicst_env_path,
        'python', unmicst,
        '-c', parsed_args.c,
        '-m', parsed_args.m
    ])

    subprocess.run([
        'conda', 'run', '--no-capture-output',
        '-p', s3seg_env_path,
        'python', s3seg,
        '-c', parsed_args.c,
        '-m', parsed_args.m
    ])

    return 0


if __name__ == '__main__':
    # python /home/ychen/mcmicro/orion-scripts/processing/run_all.py -c /home/ychen/mcmicro/orion-scripts/file_list.csv
    sys.exit(main())