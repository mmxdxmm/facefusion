import os
from typing import Optional, Tuple

import gradio
import yt_dlp

from facefusion import wording
from facefusion.filesystem import is_video
from facefusion.temp_helper import get_temp_directory_path
from facefusion.uis.core import get_ui_component

TARGET_URL_TEXTBOX : Optional[gradio.Textbox] = None
TARGET_DOWNLOAD_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global TARGET_URL_TEXTBOX
	global TARGET_DOWNLOAD_BUTTON

	TARGET_URL_TEXTBOX = gradio.Textbox(
		label = wording.get('uis.target_url_textbox'),
		max_lines = 1
	)
	TARGET_DOWNLOAD_BUTTON = gradio.Button(
		value = wording.get('uis.download_button'),
		size = 'sm'
	)


def listen() -> None:
	target_file = get_ui_component('target_file')
	preview_frame_slider = get_ui_component('preview_frame_slider')

	if target_file and preview_frame_slider:
		TARGET_DOWNLOAD_BUTTON.click(download, inputs = TARGET_URL_TEXTBOX, outputs = [target_file, preview_frame_slider])


def download(target_url : str) -> Tuple[gradio.File, gradio.Slider]:
	if target_url:
		try:
			download_options =\
			{
				'paths':
				{
					'home': os.path.join(get_temp_directory_path('download'))
				},
				'format': 'mp4'
			}

			with yt_dlp.YoutubeDL(download_options) as downloader:
				info = downloader.extract_info(target_url, download = True)
				download_file_path = downloader.prepare_filename(info)

				if is_video(download_file_path):
					return gradio.File(value = download_file_path), gradio.Slider(value = 0)
		except yt_dlp.utils.DownloadError:
			pass

	return gradio.File(value = None), gradio.Slider(value = 0)
