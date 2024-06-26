#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

import os
import torch
from utils.loss_utils import l1_loss, ssim
from gaussian_renderer import render
import sys
from scene import Scene_Vast, GaussianModel
from utils.general_utils import safe_state
from utils.image_utils import psnr
from argparse import ArgumentParser
from arguments import ModelParams, PipelineParams


def eval(dataset, pipe, args):
    gaussians = GaussianModel(dataset.sh_degree)
    
    scene = Scene_Vast(dataset, gaussians)
    bg_color = [1, 1, 1] if dataset.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")
    validation_configs = ({'name': 'test', 'cameras' : scene.getTestCameras()}, )       
    gaussians.load_ply(args.global_model_path)
    
    with torch.no_grad():
        for config in validation_configs:
            if config['cameras'] and len(config['cameras']) > 0:
                l1_test = 0.0
                psnr_test = 0.0
                for idx, viewpoint in enumerate(config['cameras']):
                    image = torch.clamp(render(viewpoint, scene.gaussians, pipe, background)["render"], 0.0, 1.0)
                    gt_image = torch.clamp(viewpoint.original_image.to("cuda"), 0.0, 1.0)
                    image = image[..., image.shape[-1]//2:]
                    gt_image = gt_image[..., gt_image.shape[-1]//2:]
                    current_l1 = l1_loss(image, gt_image).mean().double()
                    current_psnr = psnr(image, gt_image).mean().double()
                    l1_test += current_l1
                    psnr_test += current_psnr
                    print("Evaluating {}: L1 {} PSNR {}".format(viewpoint.image_name, current_l1, current_psnr))
                psnr_test /= len(config['cameras'])
                l1_test /= len(config['cameras'])          
                print("Evaluating {}: L1 {} PSNR {}".format(config['name'], l1_test, psnr_test))


if __name__ == "__main__":
    # Set up command line argument parser
    parser = ArgumentParser(description="Testing script parameters")
    lp = ModelParams(parser)
    pp = PipelineParams(parser)
    parser.add_argument('--detect_anomaly', action='store_true', default=False)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument('--global_model_path', type=str, default = None)
    args = parser.parse_args(sys.argv[1:])
    
    print("Testing " + args.model_path)

    # Initialize system state (RNG)
    safe_state(args.quiet)

    torch.autograd.set_detect_anomaly(args.detect_anomaly)
    
    eval(lp.extract(args), pp.extract(args), args)
    
    print("\nEvaluating complete.")
