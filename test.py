import argparse

import torch
import torch.distributed as dist
from torch.utils.data import DataLoader
from tqdm import tqdm

from models import MobileNetV2
from pytorch_modules.utils import Fetcher, device
from utils.datasets import ClsDataset
from utils.utils import compute_loss, compute_metrics, show_batch


@torch.no_grad()
def test(model, fetcher):
    model.eval()
    val_loss = 0
    classes = fetcher.loader.dataset.classes
    num_classes = len(classes)
    total_size = torch.Tensor([0])
    true_size = torch.Tensor([0])
    tp = torch.zeros(num_classes)
    fp = torch.zeros(num_classes)
    fn = torch.zeros(num_classes)
    pbar = tqdm(enumerate(fetcher), total=len(fetcher))
    for idx, (inputs, targets) in pbar:
        batch_idx = idx + 1
        outputs = model(inputs)
        loss = compute_loss(outputs, targets, model)
        val_loss += loss.item()
        predicted = outputs.max(1)[1]
        if idx == 0:
            show_batch(inputs.cpu(), predicted.cpu(), classes)
        eq = predicted.eq(targets)
        total_size += predicted.size(0)
        true_size += eq.sum()
        for c_i, c in enumerate(classes):
            indices = targets.eq(c_i)
            positive = indices.sum().item()
            tpi = eq[indices].sum().item()
            fni = positive - tpi
            fpi = predicted.eq(c_i).sum().item() - tpi
            tp[c_i] += tpi
            fn[c_i] += fni
            fp[c_i] += fpi
        pbar.set_description('loss: %8g, acc: %8g' %
                             (val_loss / batch_idx, true_size / total_size))
    if dist.is_initialized():
        tp = tp.to(device)
        fn = fn.to(device)
        fp = fp.to(device)
        total_size = total_size.to(device)
        true_size = true_size.to(device)
        dist.all_reduce(tp, op=dist.ReduceOp.SUM)
        dist.all_reduce(fn, op=dist.ReduceOp.SUM)
        dist.all_reduce(fp, op=dist.ReduceOp.SUM)
        dist.all_reduce(total_size, op=dist.ReduceOp.SUM)
        dist.all_reduce(true_size, op=dist.ReduceOp.SUM)
    T, P, R, F1 = compute_metrics(tp.cpu(), fn.cpu(), fp.cpu())
    if len(classes) < 10:
        for c_i, c in enumerate(classes):
            print('cls: %8s, targets: %8d, pre: %8g, rec: %8g, F1: %8g' %
                  (c, T[c_i], P[c_i], R[c_i], F1[c_i]))
    else:
        print('top error 5')
        copy_P = P.clone()
        for i in range(5):
            c_i = copy_P.min(0)[1]
            copy_P[c_i] = 1
            print('cls: %8s, targets: %8d, pre: %8g, rec: %8g, F1: %8g' %
                  (classes[c_i], T[c_i], P[c_i], R[c_i], F1[c_i]))
    return true_size.item() / total_size.item()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('val', type=str)
    parser.add_argument('--weights', type=str, default='')
    parser.add_argument('--rect', action='store_true')
    parser.add_argument('-s',
                        '--img_size',
                        type=int,
                        nargs=2,
                        default=[224, 224])
    parser.add_argument('-bs', '--batch-size', type=int, default=64)
    parser.add_argument('--num-workers', type=int, default=4)

    opt = parser.parse_args()

    val_data = ClsDataset(opt.val,
                          img_size=opt.img_size,
                          augments=None,
                          rect=opt.rect)
    val_loader = DataLoader(
        val_data,
        batch_size=opt.batch_size,
        pin_memory=True,
        num_workers=opt.num_workers,
    )
    val_fetcher = Fetcher(val_loader, post_fetch_fn=val_data.post_fetch_fn)
    model = MobileNetV2(len(val_data.classes))
    model = model.to(device)
    if opt.weights:
        state_dict = torch.load(opt.weights, map_location='cpu')
        model.load_state_dict(state_dict['model'])
    metrics = test(model, val_fetcher)
    print('metrics: %8g' % (metrics))
