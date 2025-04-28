from typing import List, Literal, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import calc_float_step
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.uis.core import get_ui_component, register_ui_component

HAIR_MODIFIER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
HAIR_MODIFIER_DIRECTION_SLIDER : Optional[gradio.Slider] = None

HairModifierModel = Literal['styleganex_hair']


def render() -> None:
	global HAIR_MODIFIER_MODEL_DROPDOWN
	global HAIR_MODIFIER_DIRECTION_SLIDER

	HAIR_MODIFIER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.hair_modifier_model_dropdown'),
		choices = processors_choices.hair_modifier_models,
		value = state_manager.get_item('hair_modifier_model'),
		visible = 'hair_modifier' in state_manager.get_item('processors')
	)
	HAIR_MODIFIER_DIRECTION_SLIDER = gradio.Slider(
		label = wording.get('uis.hair_modifier_direction_slider'),
		value = state_manager.get_item('hair_modifier_direction'),
		step = calc_float_step(processors_choices.hair_modifier_direction_range),
		minimum = processors_choices.hair_modifier_direction_range[0],
		maximum = processors_choices.hair_modifier_direction_range[-1],
		visible = 'hair_modifier' in state_manager.get_item('processors')
	)
	register_ui_component('hair_modifier_model_dropdown', HAIR_MODIFIER_MODEL_DROPDOWN)
	register_ui_component('hair_modifier_direction_slider', HAIR_MODIFIER_DIRECTION_SLIDER)


def listen() -> None:
	HAIR_MODIFIER_MODEL_DROPDOWN.change(update_hair_modifier_model, inputs = HAIR_MODIFIER_MODEL_DROPDOWN, outputs = HAIR_MODIFIER_MODEL_DROPDOWN)
	HAIR_MODIFIER_DIRECTION_SLIDER.release(update_hair_modifier_direction, inputs = HAIR_MODIFIER_DIRECTION_SLIDER)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [HAIR_MODIFIER_MODEL_DROPDOWN, HAIR_MODIFIER_DIRECTION_SLIDER])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider]:
	has_hair_modifier = 'hair_modifier' in processors
	return gradio.Dropdown(visible = has_hair_modifier), gradio.Slider(visible = has_hair_modifier)


def update_hair_modifier_model(hair_modifier_model : HairModifierModel) -> gradio.Dropdown:
	hair_modifier_module = load_processor_module('hair_modifier')
	hair_modifier_module.clear_inference_pool()
	state_manager.set_item('hair_modifier_model', hair_modifier_model)

	if hair_modifier_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('hair_modifier_model'))
	return gradio.Dropdown()


def update_hair_modifier_direction(hair_modifier_direction : float) -> None:
	state_manager.set_item('hair_modifier_direction', int(hair_modifier_direction))
