# Copyright (c) OpenMMLab. All rights reserved.
from enum import IntEnum, unique
from typing import Optional, Sequence, Union

import numpy as np
import torch
from torch import Tensor

from .base_box3d import BaseInstance3DBoxes
from .cam_box3d import CameraInstance3DBoxes
from .depth_box3d import DepthInstance3DBoxes
from .lidar_box3d import LiDARInstance3DBoxes
from .utils import limit_period


@unique
class Box3DMode(IntEnum):
    """Enum of different ways to represent a box.

    Coordinates in LiDAR:

    .. code-block:: none

                    up z
                       ^   x front
                       |  /
                       | /
        left y <------ 0

    The relative coordinate of bottom center in a LiDAR box is (0.5, 0.5, 0),
    and the yaw is around the z axis, thus the rotation axis=2.

    Coordinates in Camera:

    .. code-block:: none

                z front
               /
              /
             0 ------> x right
             |
             |
             v
        down y

    The relative coordinate of bottom center in a CAM box is (0.5, 1.0, 0.5),
    and the yaw is around the y axis, thus the rotation axis=1.

    Coordinates in Depth:

    .. code-block:: none

        up z
           ^   y front
           |  /
           | /
           0 ------> x right

    The relative coordinate of bottom center in a DEPTH box is (0.5, 0.5, 0),
    and the yaw is around the z axis, thus the rotation axis=2.
    """

    LIDAR = 0
    CAM = 1
    DEPTH = 2

    @staticmethod
    def convert(
        box: Union[Sequence[float], np.ndarray, Tensor, BaseInstance3DBoxes],
        src: 'Box3DMode',
        dst: 'Box3DMode',
        rt_mat: Optional[Union[np.ndarray, Tensor]] = None,
        with_yaw: bool = True,
        correct_yaw: bool = False
    ) -> Union[Sequence[float], np.ndarray, Tensor, BaseInstance3DBoxes]:
        """Convert boxes from ``src`` mode to ``dst`` mode.

        Args:
            box (Sequence[float] or np.ndarray or Tensor or
                :obj:`BaseInstance3DBoxes`): Can be a k-tuple, k-list or an Nxk
                array/tensor.
            src (:obj:`Box3DMode`): The source box mode.
            dst (:obj:`Box3DMode`): The target box mode.
            rt_mat (np.ndarray or Tensor, optional): The rotation and
                translation matrix between different coordinates.
                Defaults to None. The conversion from ``src`` coordinates to
                ``dst`` coordinates usually comes along the change of sensors,
                e.g., from camera to LiDAR. This requires a transformation
                matrix.
            with_yaw (bool): If ``box`` is an instance of
                :obj:`BaseInstance3DBoxes`, whether or not it has a yaw angle.
                Defaults to True.
            correct_yaw (bool): If the yaw is rotated by rt_mat.
                Defaults to False.

        Returns:
            Sequence[float] or np.ndarray or Tensor or
            :obj:`BaseInstance3DBoxes`: The converted box of the same type.
        """
        if src == dst:
            return box

        is_numpy = isinstance(box, np.ndarray)
        is_Instance3DBoxes = isinstance(box, BaseInstance3DBoxes)
        single_box = isinstance(box, (list, tuple))
        if single_box:
            assert len(box) >= 7, (
                'Box3DMode.convert takes either a k-tuple/list or '
                'an Nxk array/tensor, where k >= 7')
            arr = torch.tensor(box)[None, :]
        else:
            # avoid modifying the input box
            if is_numpy:
                arr = torch.from_numpy(np.asarray(box)).clone()
            elif is_Instance3DBoxes:
                arr = box.tensor.clone()
            else:
                arr = box.clone()

        if is_Instance3DBoxes:
            with_yaw = box.with_yaw

        # convert box from `src` mode to `dst` mode.
        x_size, y_size, z_size = arr[..., 3:4], arr[..., 4:5], arr[..., 5:6]
        if with_yaw:
            yaw = arr[..., 6:7]
        if src == Box3DMode.LIDAR and dst == Box3DMode.CAM:
            if rt_mat is None:
                rt_mat = arr.new_tensor([[0, -1, 0], [0, 0, -1], [1, 0, 0]])
            xyz_size = torch.cat([x_size, z_size, y_size], dim=-1)
            if with_yaw:
                if correct_yaw:
                    yaw_vector = torch.cat([
                        torch.cos(yaw),
                        torch.sin(yaw),
                        torch.zeros_like(yaw)
                    ],
                                           dim=1)
                else:
                    yaw = -yaw - np.pi / 2
                    yaw = limit_period(yaw, period=np.pi * 2)
        elif src == Box3DMode.CAM and dst == Box3DMode.LIDAR:
            if rt_mat is None:
                rt_mat = arr.new_tensor([[0, 0, 1], [-1, 0, 0], [0, -1, 0]])
            xyz_size = torch.cat([x_size, z_size, y_size], dim=-1)
            if with_yaw:
                if correct_yaw:
                    yaw_vector = torch.cat([
                        torch.cos(-yaw),
                        torch.zeros_like(yaw),
                        torch.sin(-yaw)
                    ],
                                           dim=1)
                else:
                    yaw = -yaw - np.pi / 2
                    yaw = limit_period(yaw, period=np.pi * 2)
        elif src == Box3DMode.DEPTH and dst == Box3DMode.CAM:
            if rt_mat is None:
                rt_mat = arr.new_tensor([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
            xyz_size = torch.cat([x_size, z_size, y_size], dim=-1)
            if with_yaw:
                if correct_yaw:
                    yaw_vector = torch.cat([
                        torch.cos(yaw),
                        torch.sin(yaw),
                        torch.zeros_like(yaw)
                    ],
                                           dim=1)
                else:
                    yaw = -yaw
        elif src == Box3DMode.CAM and dst == Box3DMode.DEPTH:
            if rt_mat is None:
                rt_mat = arr.new_tensor([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
            xyz_size = torch.cat([x_size, z_size, y_size], dim=-1)
            if with_yaw:
                if correct_yaw:
                    yaw_vector = torch.cat([
                        torch.cos(-yaw),
                        torch.zeros_like(yaw),
                        torch.sin(-yaw)
                    ],
                                           dim=1)
                else:
                    yaw = -yaw
        elif src == Box3DMode.LIDAR and dst == Box3DMode.DEPTH:
            if rt_mat is None:
                rt_mat = arr.new_tensor([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
            xyz_size = torch.cat([x_size, y_size, z_size], dim=-1)
            if with_yaw:
                if correct_yaw:
                    yaw_vector = torch.cat([
                        torch.cos(yaw),
                        torch.sin(yaw),
                        torch.zeros_like(yaw)
                    ],
                                           dim=1)
                else:
                    yaw = yaw + np.pi / 2
                    yaw = limit_period(yaw, period=np.pi * 2)
        elif src == Box3DMode.DEPTH and dst == Box3DMode.LIDAR:
            if rt_mat is None:
                rt_mat = arr.new_tensor([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
            xyz_size = torch.cat([x_size, y_size, z_size], dim=-1)
            if with_yaw:
                if correct_yaw:
                    yaw_vector = torch.cat([
                        torch.cos(yaw),
                        torch.sin(yaw),
                        torch.zeros_like(yaw)
                    ],
                                           dim=1)
                else:
                    yaw = yaw - np.pi / 2
                    yaw = limit_period(yaw, period=np.pi * 2)
        else:
            raise NotImplementedError(
                f'Conversion from Box3DMode {src} to {dst} '
                'is not supported yet')

        if not isinstance(rt_mat, Tensor):
            rt_mat = arr.new_tensor(rt_mat)
        if rt_mat.size(1) == 4:
            extended_xyz = torch.cat(
                [arr[..., :3], arr.new_ones(arr.size(0), 1)], dim=-1)
            xyz = extended_xyz @ rt_mat.t()
        else:
            xyz = arr[..., :3] @ rt_mat.t()

        # Note: we only use rotation in rt_mat
        # so don't need to extend yaw_vector
        if with_yaw and correct_yaw:
            rot_yaw_vector = yaw_vector @ rt_mat[:3, :3].t()
            if dst == Box3DMode.CAM:
                yaw = torch.atan2(-rot_yaw_vector[:, [2]], rot_yaw_vector[:,
                                                                          [0]])
            elif dst in [Box3DMode.LIDAR, Box3DMode.DEPTH]:
                yaw = torch.atan2(rot_yaw_vector[:, [1]], rot_yaw_vector[:,
                                                                         [0]])
            yaw = limit_period(yaw, period=np.pi * 2)

        if with_yaw:
            remains = arr[..., 7:]
            arr = torch.cat([xyz[..., :3], xyz_size, yaw, remains], dim=-1)
        else:
            remains = arr[..., 6:]
            arr = torch.cat([xyz[..., :3], xyz_size, remains], dim=-1)

        # convert arr to the original type
        original_type = type(box)
        if single_box:
            return original_type(arr.flatten().tolist())
        if is_numpy:
            return arr.numpy()
        elif is_Instance3DBoxes:
            if dst == Box3DMode.CAM:
                target_type = CameraInstance3DBoxes
            elif dst == Box3DMode.LIDAR:
                target_type = LiDARInstance3DBoxes
            elif dst == Box3DMode.DEPTH:
                target_type = DepthInstance3DBoxes
            else:
                raise NotImplementedError(
                    f'Conversion to {dst} through {original_type} '
                    'is not supported yet')
            return target_type(arr, box_dim=arr.size(-1), with_yaw=with_yaw)
        else:
            return arr
