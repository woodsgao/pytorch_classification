import torch
import torch.nn as nn
from . import DBL, EmptyLayer


class CutLayer(nn.Module):
    def __init__(self, cut_idx):
        super(CutLayer, self).__init__()
        self.cut_idx = cut_idx

    def forward(self, x):
        return x[:, :self.cut_idx]


class DenseBlock(nn.Module):
    def __init__(self,
                 in_channels,
                 out_channels,
                 stride=1,
                 dilation=1,
                 drop_rate=0.5,
                 se_block=False):
        super(DenseBlock, self).__init__()
        assert in_channels == out_channels or 2 * in_channels == out_channels
        assert in_channels % 2 == 0
        assert stride == 1 or stride == 2
        out_channels = out_channels // 2
        if stride == 1:
            self.downsample = CutLayer(out_channels)
        else:
            self.downsample = DBL(in_channels, out_channels, 1, 2)
        self.block = nn.Sequential(
            DBL(in_channels, out_channels // 2, 1),
            DBL(
                out_channels // 2,
                out_channels // 2,
                stride=stride,
                dilation=dilation,
                groups=out_channels // 2,
            ),
            DBL(
                out_channels // 2,
                out_channels,
                1,
            ),
            nn.Dropout(drop_rate) if drop_rate > 0 else EmptyLayer(),
        )

    def forward(self, x):
        x = torch.cat([self.downsample(x), self.block(x)], 1)
        return x
