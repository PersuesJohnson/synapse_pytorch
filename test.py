import os, sys
import numpy as np
import pickle, h5py, time, argparse, itertools, datetime

import torch
import torch.nn as nn
import torch.utils.data
from libs import SynapseDataset, collate_fn_test, res_unet

def get_args():
    parser = argparse.ArgumentParser(description='Testing Model')
    # I/O
    parser.add_argument('-t','--train',  default='/n/coxfs01/',
                        help='input folder (train)')
    parser.add_argument('-v','--val',  default='',
                        help='input folder (test)')
    parser.add_argument('-dn','--img-name',  default='im_uint8.h5',
                        help='image data')
    parser.add_argument('-o','--output', default='result/train/',
                        help='output path')
    parser.add_argument('-mi','--model-input', type=str,  default='31,204,204')

    # machine option
    parser.add_argument('-g','--num-gpu', type=int,  default=1,
                        help='number of gpu')
    parser.add_argument('-c','--num-cpu', type=int,  default=1,
                        help='number of cpu')
    parser.add_argument('-b','--batch-size', type=int,  default=1,
                        help='batch size')
    parser.add_argument('-m','--model', help='model used for test')
    args = parser.parse_args()
    return args

def init(args):
    sn = args.output+'/'
    if not os.path.isdir(sn):
        os.makedirs(sn)
    # I/O size in (z,y,x), no specified channel number
    model_io_size = np.array([int(x) for x in args.model_input.split(',')])

    # select training machine
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    return model_io_size, device

def get_input(args, model_io_size, opt='test'):
    # two dataLoader, can't be both multiple-cpu (pytorch issue)

    dir_name = args.train.split('@')
    num_worker = args.num_cpu
    img_name = args.img_name.split('@')

    # may use datasets from multiple folders
    # should be either one or the same as dir_name
    img_name = [dir_name[0] + x for x in img_name]
    
    # 1. load data
    print('number of volumes:', len(img_name))
    test_input = [None]*len(img_name)
    result = [None]*len(img_name)
    weight = [None]*len(img_name)

    # original image is in [0, 255], normalize to [0, 1]
    for i in range(len(img_name)):
        test_input[i] = np.array(h5py.File(img_name[i], 'r')['main'])/255.0
        # test_input[i] = np.transpose(test_input[i], (2,0,1))
        print("volume shape: ", test_input[i].shape)
        result[i] = np.zeros(test_input[i].shape)
        weight[i] = np.zeros(test_input[i].shape)

    dataset = SynapseDataset(volume=test_input, label=None, vol_input_size=model_io_size, \
                             vol_label_size=None, sample_stride=model_io_size/2, \
                             data_aug=None, mode='test')
    # to have evaluation during training (two dataloader), has to set num_worker=0
    SHUFFLE = (opt=='train')
    img_loader =  torch.utils.data.DataLoader(
            dataset, batch_size=args.batch_size, shuffle=SHUFFLE, collate_fn = collate_fn_test,
            num_workers=args.num_cpu, pin_memory=True)
    return img_loader, result, weight

def blend(sz, opt=0):
    bw = 0.02 # border weight
    if opt==0:
        zz = np.append(np.linspace(1-bw,bw,sz[0]/2), np.linspace(bw,1-bw,sz[0]/2))
        yy = np.append(np.linspace(1-bw,bw,sz[1]/2), np.linspace(bw,1-bw,sz[1]/2))
        xx = np.append(np.linspace(1-bw,bw,sz[2]/2), np.linspace(bw,1-bw,sz[2]/2))
        zv, yv, xv = np.meshgrid(zz, yy, xx, indexing='ij')
        temp = np.stack([zv, yv, xv], axis=0)
        ww = 1-np.max(temp, 0)

    elif opt==1:
        zz = np.append(np.linspace(bw,1-bw,sz[0]/2), np.linspace(bw,1-bw,sz[0]/2))
        yy = np.append(np.linspace(bw,1-bw,sz[1]/2), np.linspace(bw,1-bw,sz[1]/2))
        xx = np.append(np.linspace(bw,1-bw,sz[2]/2), np.linspace(bw,1-bw,sz[2]/2))
        zv, yv, xv = np.meshgrid(zz, yy, xx, indexing='ij')
        ww = (zv + yv + xv)/3

    return ww

def test(args, test_loader, result, weight, model, device, model_io_size):
    # switch to eval mode
    model.eval()
    volume_id = 0
    ww = blend(model_io_size, 0)

    start = time.time()
    with torch.no_grad():
        for i, (pos, volume) in enumerate(test_loader):
            volume_id += args.batch_size
            print('volume_id:', volume_id)

            # for gpu computing
            volume = volume.to(device)
            output = model(volume)
            if i==0: 
                print("volume size:", volume.size())
                print("output size:", output.size())

            sz = model_io_size
            for idx in range(args.batch_size):
                st = pos[idx]
                result[st[0]][st[1]:st[1]+sz[0], st[2]:st[2]+sz[1], \
                st[3]:st[3]+sz[2]] += output[idx].cpu().detach().numpy().reshape(sz) * ww
                weight[st[0]][st[1]:st[1]+sz[0], st[2]:st[2]+sz[1], \
                st[3]:st[3]+sz[2]] += ww

    end = time.time()
    print("prediction time:", (end-start))

    for vol_id in range(len(result)):
        result[vol_id] = result[vol_id] / weight[vol_id]
        #data = (result[vol_id]*255).astype(np.uint8)
        #data[data < 128] = 0
        hf = h5py.File(args.output+'/volume_'+str(vol_id)+'.h5','w')
        hf.create_dataset('main', data=result[vol_id])
        hf.close()


def main():
    args = get_args()

    print('0. initial setup')
    model_io_size, device = init(args)
    print('model I/O size:', model_io_size) 

    print('1. setup data')
    test_loader, result, weight = get_input(args, model_io_size, 'test')

    print('2. setup model')
    print(args.model)
    model = res_unet()
    model.load_state_dict(torch.load(args.pre_model))
    # model = torch.load(args.model)
    # still some problems in multi-gpu testing
    if args.num_gpu>1: model = nn.DataParallel(model, range(args.num_gpu))
    model = model.to(device)

    print('3. start testing')
    test(args, test_loader, result, weight, model, device, model_io_size)
  
    print('4. finish testing')

if __name__ == "__main__":
    main()
