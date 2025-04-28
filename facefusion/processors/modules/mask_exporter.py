from argparse import ArgumentParser
from typing import List, TypedDict

import cv2
import numpy

import facefusion.processors.core as processors
from facefusion import content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, process_manager, state_manager
from facefusion.face_analyser import get_many_faces, get_one_face
from facefusion.face_helper import warp_face_by_face_landmark_5
from facefusion.face_masker import create_occlusion_mask, create_region_mask, create_static_box_mask
from facefusion.face_selector import find_similar_faces, sort_and_filter_faces
from facefusion.face_store import get_reference_faces
from facefusion.typing import ApplyStateItem, Args, Face, FaceSet, InferencePool, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import read_image, read_static_image, write_image

MaskExporterInputs = TypedDict('MaskExporterInputs',
{
	'reference_faces' : FaceSet,
	'target_vision_frame' : VisionFrame
})


def get_inference_pool() -> InferencePool:
	pass


def clear_inference_pool() -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	pass


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	pass


def pre_check() -> bool:
	return True


def pre_process(mode : ProcessMode) -> bool:
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()
		face_classifier.clear_inference_pool()
		face_detector.clear_inference_pool()
		face_landmarker.clear_inference_pool()
		face_masker.clear_inference_pool()
		face_recognizer.clear_inference_pool()


def export_mask(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), 'arcface_128_v2', (512, 512))
	crop_masks = []

	if 'box' in state_manager.get_item('face_mask_types'):
		box_mask = create_static_box_mask(crop_vision_frame.shape[:2][::-1], state_manager.get_item('face_mask_blur'), state_manager.get_item('face_mask_padding'))
		crop_masks.append(box_mask)

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		crop_masks.append(occlusion_mask)

	if 'region' in state_manager.get_item('face_mask_types'):
		region_mask = create_region_mask(crop_vision_frame, state_manager.get_item('face_mask_regions'))
		crop_masks.append(region_mask)

	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
	inverse_matrix = cv2.invertAffineTransform(affine_matrix)
	temp_vision_frame = cv2.warpAffine(crop_mask, inverse_matrix, temp_vision_frame.shape[:2][::-1])
	temp_vision_frame = cv2.cvtColor(temp_vision_frame, cv2.COLOR_GRAY2BGR) * 255
	temp_vision_frame = temp_vision_frame.astype(numpy.uint8)
	return temp_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(inputs : MaskExporterInputs) -> VisionFrame:
	reference_faces = inputs.get('reference_faces')
	target_vision_frame = inputs.get('target_vision_frame')
	many_faces = sort_and_filter_faces(get_many_faces([ target_vision_frame ]))
	mask_vision_frames = []

	if state_manager.get_item('face_selector_mode') == 'many':
		if many_faces:
			for target_face in many_faces:
				mask_vision_frame = export_mask(target_face, target_vision_frame)
				mask_vision_frames.append(mask_vision_frame)
			target_vision_frame = numpy.maximum.reduce(mask_vision_frames).clip(0, 255)
	if state_manager.get_item('face_selector_mode') == 'one':
		target_face = get_one_face(many_faces)
		if target_face:
			mask_vision_frame = export_mask(target_face, target_vision_frame)
			mask_vision_frames.append(mask_vision_frame)
	if state_manager.get_item('face_selector_mode') == 'reference':
		similar_faces = find_similar_faces(many_faces, reference_faces, state_manager.get_item('reference_face_distance'))
		if similar_faces:
			for similar_face in similar_faces:
				mask_vision_frame = export_mask(similar_face, target_vision_frame)
				mask_vision_frames.append(mask_vision_frame)
	if mask_vision_frames:
		target_vision_frame = numpy.maximum.reduce(mask_vision_frames).clip(0, 255)
	else:
		target_vision_frame = numpy.zeros_like(target_vision_frame)
	return target_vision_frame


def process_frames(source_paths : List[str], queue_payloads : List[QueuePayload], update_progress : UpdateProgress) -> None:
	reference_faces = get_reference_faces() if 'reference' in state_manager.get_item('face_selector_mode') else None

	for queue_payload in process_manager.manage(queue_payloads):
		target_vision_path = queue_payload['frame_path']
		target_vision_frame = read_image(target_vision_path)
		output_vision_frame = process_frame(
		{
			'reference_faces': reference_faces,
			'target_vision_frame': target_vision_frame
		})
		write_image(target_vision_path, output_vision_frame)
		update_progress(1)


def process_image(source_paths : List[str], target_path : str, output_path : str) -> None:
	reference_faces = get_reference_faces() if 'reference' in state_manager.get_item('face_selector_mode') else None
	target_vision_frame = read_static_image(target_path)
	output_vision_frame = process_frame(
	{
		'reference_faces': reference_faces,
		'target_vision_frame': target_vision_frame
	})
	write_image(output_path, output_vision_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	processors.multi_process_frames(source_paths, temp_frame_paths, process_frames)
