# Copyright (c) OpenMMLab. All rights reserved.
from typing import Sequence

from mmcv.cnn.bricks import ConvModule
from torch import Tensor

from mmdet3d.models.layers import DGCNNFPModule
from mmdet3d.registry import MODELS
from .decode_head import Base3DDecodeHead


@MODELS.register_module()
class DGCNNHead(Base3DDecodeHead):
    r"""DGCNN decoder head.

    Decoder head used in `DGCNN <https://arxiv.org/abs/1801.07829>`_.
    Refer to the
    `reimplementation code <https://github.com/AnTao97/dgcnn.pytorch>`_.

    Args:
        fp_channels (Sequence[int]): Tuple of mlp channels in feature
            propagation (FP) modules. Defaults to (1216, 512).
    """

    def __init__(self, fp_channels: Sequence[int] = (1216, 512),
                 **kwargs) -> None:
        super(DGCNNHead, self).__init__(**kwargs)

        self.FP_module = DGCNNFPModule(
            mlp_channels=fp_channels, act_cfg=self.act_cfg)

        # https://github.com/charlesq34/pointnet2/blob/master/models/pointnet2_sem_seg.py#L40
        self.pre_seg_conv = ConvModule(
            fp_channels[-1],
            self.channels,
            kernel_size=1,
            bias=False,
            conv_cfg=self.conv_cfg,
            norm_cfg=self.norm_cfg,
            act_cfg=self.act_cfg)

    def _extract_input(self, feat_dict: dict) -> Tensor:
        """Extract inputs from features dictionary.

        Args:
            feat_dict (dict): Feature dict from backbone.

        Returns:
            torch.Tensor: Points for decoder.
        """
        fa_points = feat_dict['fa_points']

        return fa_points

    def forward(self, feat_dict: dict) -> Tensor:
        """Forward pass.

        Args:
            feat_dict (dict): Feature dict from backbone.

        Returns:
            Tensor: Segmentation map of shape [B, num_classes, N].
        """
        fa_points = self._extract_input(feat_dict)

        fp_points = self.FP_module(fa_points)
        fp_points = fp_points.transpose(1, 2).contiguous()
        output = self.pre_seg_conv(fp_points)
        output = self.cls_seg(output)

        return output
