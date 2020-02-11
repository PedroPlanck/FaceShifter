import sys
sys.path.append('../')
import torch
import torchvision.transforms as transforms
import torch.nn.functional as F
from face_modules.model import Backbone, Arcface, MobileFaceNet, Am_softmax, l2_norm
from network.AEI_Net import *
from face_modules.mtcnn import *
import cv2
import PIL.Image as Image
import numpy as np
import glob
import time
import os


output_path = '~/hearnet_data/'
os.makedirs(output_path, exist_ok=True)


device = torch.device('cuda')
G = AEI_Net(c_id=512)
G.eval()
G.load_state_dict(torch.load('../saved_models/G_latest.pth', map_location=torch.device('cpu')))
G = G.cuda()

arcface = Backbone(50, 0.6, 'ir_se').to(device)
arcface.eval()
arcface.load_state_dict(torch.load('../face_modules/model_ir_se50.pth', map_location=device), strict=False)

test_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

data_roots = ['../../celeb-aligned-256_0.85/', '../../ffhq_256_0.85/', '../../vgg_256_0.85/', '../../stars_256_0.85/']

all_lists = []
for data_root in data_roots:
    img_lists = glob.glob(data_root + '/*.*g')
    all_lists.extend(img_lists)

scores = []

with torch.no_grad():
    for idx, img_path in enumerate(all_lists):
        print(f'{idx} / {len(all_lists)}')
        img = cv2.imread(img_path)[:,:,::-1]
        X = Image.fromarray(img)
        X = test_transform(X)
        X = X.unsqueeze(0).cuda()
        embeds, _ = arcface(F.interpolate(X[:, :, 19:237, 19:237], (112, 112), mode='bilinear', align_corners=True))
        Yt, _ = G(X, embeds)
        HE = torch.abs(X - Yt).mean()
        scores.append((img_path, HE.item()))


    def comp(x):
        return x[1]


    scores.sort(key=comp, reverse=True)
    N = len(scores)
    pick_num = int(N*0.1)
    scores = scores[:pick_num]

    ind = 0
    print('copying files...')
    for img_path, _ in scores:
        os.system(f'cp {img_path} {output_path}/%08d.jpg'%ind)
        ind += 1
        # test bug
        # img = cv2.imread(img_path)[:, :, ::-1]
        # X = Image.fromarray(img)
        # X = test_transform(X)
        # X = X.unsqueeze(0).cuda()
        # embeds, _ = arcface(F.interpolate(X[:, :, 19:237, 19:237], (112, 112), mode='bilinear', align_corners=True))
        # Yt, _ = G(X, embeds)
        # X = X.cpu().numpy().transpose(2, 3, 1, 0).squeeze()
        # Yt = Yt.cpu().numpy().transpose(2, 3, 1, 0).squeeze()
        # X = (X*0.5)+0.5
        # Yt = (Yt*0.5)+0.5
        # show = np.concatenate((X, Yt), axis=1)[:,:,::-1]
        # cv2.imshow('show', show)
        # cv2.waitKey(0)
    print('done')
