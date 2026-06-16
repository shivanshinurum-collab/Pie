import torch
from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_pretrained(
    "segmind/tiny-sd",
    torch_dtype=torch.float32,
    safety_checker=None,
    requires_safety_checker=False,
)

# CPU only
pipe = pipe.to("cpu")

image = pipe(
    "boy and girl holding hands, standing together on a mountain cliff, looking at mountains, sunset, romantic scene, realistic photo",
    num_inference_steps=4,
    guidance_scale=5,
    height=256,
    width=256,
).images[0]

image.save("output.png")
print("Done")



# from diffusers import FluxPipeline
# import torch
# import os

# os.makedirs("media", exist_ok=True)

# pipe = FluxPipeline.from_pretrained(
#     "black-forest-labs/FLUX.1-dev",
#     torch_dtype=torch.bfloat16
# )

# pipe.enable_model_cpu_offload()

# image = pipe(
#     "A futuristic AI engineer working on multiple monitors, ultra realistic"
# ).images[0]

# image.save("media/generated.png")

# print("Done!")