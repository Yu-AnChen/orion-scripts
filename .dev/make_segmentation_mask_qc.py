import skimage.io
import pathlib
import numpy as np
import skimage.segmentation
from subprocess import call

def main(mask_path, img_path, out_name, img_channel=0, out_dir='.'):
    print('Processing', img_path, '->', out_name)
    mask_path = pathlib.Path(mask_path)
    img_path = pathlib.Path(img_path)
    out_dir = pathlib.Path(out_dir)

    mask = skimage.io.imread(str(mask_path))
    bounds = skimage.segmentation.find_boundaries(mask)
    del mask
    bounds = skimage.img_as_uint(bounds)
    bounds[bounds == 65535] = 65535-25535

    bounds_out_path = out_dir / '01-{}.tif'.format(mask_path.stem)
    skimage.io.imsave(
        str(bounds_out_path),
        bounds,
        metadata=None, bigtiff=True, check_contrast=False
    )
    del bounds

    img = skimage.io.imread(str(img_path), key=img_channel)
    img_out_path = out_dir / '00-{}-ch_{}.tif'.format(img_path.stem, img_channel)
    skimage.io.imsave(
        str(img_out_path),
        img,
        metadata=None, bigtiff=True, check_contrast=False
    )
    call('python pyramid_assemble.py {} {} {} --pixel-size {}'.format(
        img_out_path, bounds_out_path, out_dir / out_name, 0.325
    ))

import csv

with open(r'Z:\RareCyte-S3\YC-analysis\P37_CRCstudy_Round1\scripts-processing\file_list.csv') as file_config_csv:
    csv_reader = csv.DictReader(file_config_csv)
    file_config = [dict(row) for row in csv_reader]

group_dir = pathlib.Path(r'Z:\RareCyte-S3\YC-analysis\P37_CRCstudy_Round1')
ome_dir = pathlib.Path(r'Z:\RareCyte-S3\P37_CRCstudy_Round1')

out_dir = pathlib.Path(r'D:\yc296\RC')

for c in file_config[:2]:
    o = ome_dir / c['path']
    n = c['name']
    m = str(
        group_dir /
        n /
        'segmentation' /
        c['path'].replace('.ome.tiff', '') /
        'cellRingMask.tif'
    )
    d = out_dir / n
    # if d.exists():
    #     print(f'    Already exists ({d})')
    #     continue
    
    d.mkdir(exist_ok=True, parents=True)
    main(
        m,
        o,
        f'{n}-cellRingMask-qc.ome.tif',
        img_channel=0,
        out_dir=d
    )


# ome_tiffs = [pathlib.Path(c['path']) for c in file_config]
# ome_names = [n.stem.replace('.ome', '') for n in ome_tiffs]
# slide_names = [pathlib.Path(c['name']) for c in file_config]

# group_dir = pathlib.Path(r'Z:\RareCyte-S3\YC-analysis\Lung_066-082')

# mask_paths = [
#     group_dir / s_n / 'segmentation' / o_n / 'cellRingMask.tif'
#     for s_n, o_n in zip(slide_names, ome_names)
# ]

# out_dirs = [
#     pathlib.Path(r'D:\yc296\RC') / s_n
#     for s_n in slide_names
# ]    


# for m, o, s, d in zip(
#     mask_paths[:1],
#     ome_tiffs[:1],
#     slide_names[:1],
#     out_dirs[:1]
# ):
#     print('Processing', s.name)
#     if d.exists():
#         print('    Already exists')
#         continue
    
#     d.mkdir(exist_ok=True, parents=True)
#     main(m, r'Z:\RareCyte-S3' / o, '{}-cellRingMask-qc.ome.tif'.format(s), img_channel=0, out_dir=d)
#     print()