!pip install diffusers transformers accelerate
import torch
from diffusers import DiffusionPipeline,DPMSolverMultistepScheduler
from diffusers.utils import export_to_video

pipe=DiffusionPipeline.from_pretrained("damo-vilab/text-to-video-ms-1.7b",torch_dtype = torch.float16, variant="fp16")
pipe.scheduler=DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_model_cpu_offload()
prompt= "narendra modi leads to talk on pgii"
video_frames=pipe(prompt,num_inference_steps=25).frames
video_path=export_to_video(video_frames)
video_name=video_path.replace('/tmp','')
print('Name:',video_name)
torch.cuda.empty_cache()
