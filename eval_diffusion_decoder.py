import glob
from PIL import Image
import numpy as np
from omegaconf import OmegaConf
from pytorch_lightning import Trainer
import torch
from torchvision.utils import save_image
from torch import autocast
import math
from dataclasses import asdict
from einops import rearrange, repeat
from torch.utils.data import DataLoader, Dataset
import pytorch_lightning as pl
from torchmetrics.functional.image.lpips import learned_perceptual_image_patch_similarity
from torchmetrics.image import PeakSignalNoiseRatio
from torchmetrics.functional.image import structural_similarity_index_measure
from dataloaders.coco17_loader import COCO17Loader, COCO17Val
from dataloaders.imagenet_loader import ImageNetLatentLoader
from diffusion_decoder import DecodingUnetConcat
from eval.reconstruction_eval import ReconstructionEval
from generate_new_decoder import generate_from_decoder
from generative_models.sgm.inference.api import (
    SamplingParams,
    SamplingPipeline,
    SamplingSpec,
    ModelArchitecture,
)
import cv2
import generative_models.sgm.inference.helpers as helpers
import generative_models.sgm.inference.api as api
from sgm.modules.diffusionmodules.guiders import LinearPredictionGuider, VanillaCFG
from sgm.modules.diffusionmodules.sampling import EulerEDMSampler
from sgm.util import append_dims, instantiate_from_config

from generative_models.sgm.util import disabled_train, load_model_from_config
from tqdm import tqdm
import glob

device = "cuda"
seed = 42
torch.manual_seed(seed)

# ==== VAE ====
# model_config = OmegaConf.load("configs/models/cifar10_model.yaml")
# diffusion_decoder = load_model_from_config(model_config.first_stage_config, "checkpoints/sdxl_vae.safetensors")
# diffusion_decoder = diffusion_decoder.to("cuda")

# ==== Diffusion Decoder ====
model_config = OmegaConf.load("configs/models/ddpm_diffusion_decoder.yaml")
diffusion_decoder = instantiate_from_config(model_config.model)
sampler = instantiate_from_config(model_config.model.params.sampler_config)
checkpoint_path = glob.glob("lightning_logs/version_136/checkpoints/*.ckpt")[0]
diffusion_decoder = diffusion_decoder.load_from_checkpoint(
    checkpoint_path,
    network_config=model_config.model.params.network_config,
    denoiser_config=model_config.model.params.denoiser_config,
    conditioner_config=model_config.model.params.conditioner_config,
    first_stage_config=model_config.model.params.first_stage_config,
    loss_fn_config=model_config.model.params.loss_fn_config,
    sampler_config=model_config.model.params.sampler_config,
)
diffusion_decoder = diffusion_decoder.to(device)
diffusion_decoder.learning_rate = model_config.model.base_learning_rate

loader = ImageNetLatentLoader(1, 10, test_frac=0.9900, dims=(128, 128), random_seed=2024, shuffle=False)

with torch.no_grad():
    smpls = torch.Tensor([]).to("cuda")
    orig = torch.Tensor([]).to("cuda")
    i = 0
    h = 0
    for dl_batch in tqdm(loader.val_dataloader()):
        if i < 50:
            i += 1
            continue
        samples = generate_from_decoder(diffusion_decoder, sampler, dl_batch["ltnt"].to(device), img_dims=128)
        # samples = diffusion_decoder.decode(dl_batch["ltnt"].to(device))
        # samples = torch.clamp((samples + 1.0) / 2.0, min=0.0, max=1.0).to("cuda")
        orig_images = torch.clamp((dl_batch["jpg"] + 1.0) / 2.0, min=0.0, max=1.0).to("cuda")
        smpls = torch.cat([smpls, samples], dim=0)
        orig = torch.cat([orig, orig_images], dim=0)

        h += 1

        if h >= 4:
            break
    
    i = 0
    h = 0
    for dl_batch in tqdm(loader.train_dataloader()):
        if i < 50:
            i += 1
            continue
        samples = generate_from_decoder(diffusion_decoder, sampler, dl_batch["ltnt"].to(device), img_dims=128)
        # samples = diffusion_decoder.decode(dl_batch["ltnt"].to(device))
        # samples = torch.clamp((samples + 1.0) / 2.0, min=0.0, max=1.0).to("cuda")
        orig_images = torch.clamp((dl_batch["jpg"] + 1.0) / 2.0, min=0.0, max=1.0).to("cuda")
        smpls = torch.cat([smpls, samples], dim=0)
        orig = torch.cat([orig, orig_images], dim=0)
        
        h += 1

        if h >= 4:
            break

    recon_evaluator = ReconstructionEval("cuda")
    evaluation_train = recon_evaluator(smpls[4:], orig[4:].to("cuda"))
    evaluation_val = recon_evaluator(smpls[:4], orig[:4].to("cuda"))

    print("Train eval:", evaluation_train)
    print("Test eval", evaluation_val)

    save_image(smpls.to("cpu"), 'decoded_unet_img_ddpm_val+train.png')
    save_image(orig.to("cpu"), 'decoded_unet_img_orig_ddpm_val+train.png')