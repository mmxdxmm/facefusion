from functools import lru_cache

from facefusion import inference_manager, state_manager

PROBABILITY_LIMIT = 1.00
RATE_LIMIT = 10
STREAM_COUNTER = 0

def create_static_model_set(download_scope):
	return {}

def check_static_model_set(model_set):
	pass

def process_frame_static(pool, frame, frame_count, fps):
	pass

def process_video_static(pool, video_path):
	pass

def analyse_content_static(video_path):
	pass

def analyse_image(image_path):
	pass  # No-op placeholder

def analyse_video(video_path, trim_frame_start=None, trim_frame_end=None):
	pass  # No-op placeholder

def pre_check():
	return True  # Placeholder that always succeeds

def clear_inference_pool():
	"""Clear the inference pool resources for content_analyser."""
	inference_manager.clear_inference_pool(__name__)
