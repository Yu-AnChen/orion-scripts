import configparser
import csv
import datetime
import pathlib


def process_arg_path(path):
    path = pathlib.Path(path)
    if path.suffix == '.csv':
        with open(path) as file_config_csv:
            csv_reader = csv.DictReader(file_config_csv)
            return sanitize_config([dict(row) for row in csv_reader])
    ometiff = sorted(path.glob('*.ome.tiff'))
    if len(ometiff) == 0:
        ometiff = sorted(path.glob('*.ome.tif'))
    if len(ometiff) == 0:
        print(f"no .ome.tiff or .ome.tif found in {path}")
        return
    return [{'path': pp} for pp in ometiff]


def sanitize_config(config):
    for idx, cc in enumerate(config):
        for key, value in cc.items():
            assert value is not None, (
                f"{key} column does not have a value at row {idx+1}"
            )
    return config


def set_config_defaults(config):
    assert 'path' in config, 'must at least contain path to ome-tiff'
    path = pathlib.Path(config['path'])
    return {
        'path': path,
        'name': config.get('name', path.stem.replace('.ome', '')),
        'out_dir': pathlib.Path(config.get('out_dir', path.parent))
    }


def to_log(log_path, img_path, time_diff, kwargs):
    import tifffile
    img_path = pathlib.Path(img_path)
    with tifffile.TiffFile(img_path) as tif:
        shape = tif.series[0].shape
    arg_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
    with open(log_path, 'a') as log_file:
        log_file.write(
            f"{datetime.timedelta(seconds=time_diff)} | {img_path.name} | {shape} | {arg_str}\n"
        )


def init_run(
    parsed_args, module_defaults, module_name
):
    
    CURR = pathlib.Path(__file__).resolve().parent

    ini_config = configparser.ConfigParser(allow_no_value=True)
    ini_config.read(CURR / 'run_all.ini')

    module_cfg = ini_config[module_name]
    
    module_params = {
        k: getattr(module_cfg, f"get{t}")(k, fallback=v)
        for k, v, t in module_defaults
    }

    # use custom params if `-m` is specified
    custom_params = {}
    log_path = None
    if parsed_args.m is not None:
        custom_config = configparser.ConfigParser(allow_no_value=True)
        custom_config.read(parsed_args.m)

        custom_params = {
            k: getattr(custom_config[module_name], f"get{t}")(k, fallback=v)
            for k, v, t in module_defaults
        }
        if 'log path' in custom_config:
            log_path = custom_config['log path'].get(
                module_name, fallback=None
            )
    module_params.update(custom_params)
    
    log_path = ini_config['log path'].get(module_name, log_path)
    if log_path is None:
        log_path = CURR.parent / f".log/{module_name}.log"
    log_path = pathlib.Path(log_path)
    log_path.parent.mkdir(exist_ok=True, parents=True)

    file_config = process_arg_path(parsed_args.c)


    return file_config, module_params, log_path