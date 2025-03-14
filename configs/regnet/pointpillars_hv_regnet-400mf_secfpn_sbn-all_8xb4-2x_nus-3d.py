_base_ = './pointpillars_hv_regnet-400mf_fpn_sbn-all_8xb4-2x_nus-3d.py'
# model settings
model = dict(
    pts_neck=dict(
        type='SECONDFPN',
        _delete_=True,
        norm_cfg=dict(type='naiveSyncBN2d', eps=1e-3, momentum=0.01),
        in_channels=[64, 160, 384],
        upsample_strides=[1, 2, 4],
        out_channels=[128, 128, 128]),
    pts_bbox_head=dict(
        type='Anchor3DHead',
        in_channels=384,
        feat_channels=384,
        anchor_generator=dict(
            _delete_=True,
            type='AlignedAnchor3DRangeGenerator',
            ranges=[
                [-49.6, -49.6, -1.80032795, 49.6, 49.6, -1.80032795],
                [-49.6, -49.6, -1.74440365, 49.6, 49.6, -1.74440365],
                [-49.6, -49.6, -1.68526504, 49.6, 49.6, -1.68526504],
                [-49.6, -49.6, -1.67339111, 49.6, 49.6, -1.67339111],
                [-49.6, -49.6, -1.61785072, 49.6, 49.6, -1.61785072],
                [-49.6, -49.6, -1.80984986, 49.6, 49.6, -1.80984986],
                [-49.6, -49.6, -1.763965, 49.6, 49.6, -1.763965],
            ],
            sizes=[
                [4.60718145, 1.95017717, 1.72270761],  # car
                [6.73778078, 2.4560939, 2.73004906],  # truck
                [12.01320693, 2.87427237, 3.81509561],  # trailer
                [1.68452161, 0.60058911, 1.27192197],  # bicycle
                [0.7256437, 0.66344886, 1.75748069],  # pedestrian
                [0.40359262, 0.39694519, 1.06232151],  # traffic_cone
                [0.48578221, 2.49008838, 0.98297065],  # barrier
            ],
            custom_values=[0, 0],
            rotations=[0, 1.57],
            reshape_out=True)))
