import argparse
from tqdm import tqdm
import os
import json
import time
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from shapely import box, multipoints
from ocr import merge_subword, word_labels_list_to_coco_dict

def get_azure_ocr_word(client, filename_path):
	word_labels = []

	read_image = open(filename_path, "rb")
	# Call API with image and raw response (allows you to get the operation location)
	read_response = client.read_in_stream(read_image, raw=True)
	# Get the operation location (URL with ID as last appendage)
	read_operation_location = read_response.headers["Operation-Location"]
	# Take the ID off and use to get results
	operation_id = read_operation_location.split("/")[-1]

	# Call the "GET" API and wait for the retrieval of the results
	while True:
		read_result = client.get_read_result(operation_id)
		if read_result.status.lower() not in ['notstarted', 'running']:
			break
		print('Waiting for result...')
		time.sleep(10)

	# Print results, line by line
	if read_result.status == OperationStatusCodes.succeeded:
		for text_result in read_result.analyze_result.read_results:
			for line in text_result.lines:
				for word in line.words:
					label = {'text': word.text}
					xy1 = word.bounding_box[0:2]
					xy2 = word.bounding_box[4:6]
					label['bb'] = tuple(map(int, (xy1[0], xy1[1], xy2[0], xy2[1])))
					label['bb_shapely'] = box(xy1[0], xy1[1], xy2[0], xy2[1])
					label['ul_shapely'] = multipoints([[xy1[0], xy2[1]], [xy2[0], xy2[1]]])
					word_labels.append(label)
	return word_labels

def export_azure_ocr_as_json():
	subscription_key = os.environ["VISION_KEY"]
	endpoint = os.environ["VISION_ENDPOINT"]
	client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

	data = []
	dirname, _, filenames = next(os.walk(opt.source))
	for filename in tqdm(filenames):
		if filename.endswith('.png') or filename.endswith('.jpg'):
			filename_path = os.path.join(dirname, filename)
			word_labels = get_azure_ocr_word(client, filename_path)
			merged_word_labels = merge_subword(word_labels)
			data.append({'filename_path':filename_path, 'word_labels':merged_word_labels})

	# create a file to import into Label Studio
	with open(os.path.join(opt.source,'labels.json'), mode='w') as f:
		json.dump(word_labels_list_to_coco_dict(data), f, indent=2)

def set_key():
	os.environ["VISION_KEY"] = "31448cea13684055978a88efcb82112c"
	os.environ["VISION_ENDPOINT"] = "https://iacquisition.cognitiveservices.azure.com/"

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--source', type=str, default='.', help='source')  # file/folder, 0 for webcam.
	opt = parser.parse_args()
	print(opt)
	set_key()
	export_azure_ocr_as_json()
