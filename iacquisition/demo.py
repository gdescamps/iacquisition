import streamlit as st
import torch
from llava.model.builder import load_pretrained_model
from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
from llava.conversation import conv_templates, SeparatorStyle
from llava.mm_utils import tokenizer_image_token, get_model_name_from_path, KeywordsStoppingCriteria
from PIL import Image

@st.cache_resource
def create_llava_model(devices=['0']):
    model_path = './models/llava-v1.5-7b/'
    tokenizer, model, image_processor, context_len = load_pretrained_model(model_path, None, 'llava-v1.5-7b', load_4bit=True)
    return tokenizer, model, image_processor, context_len

# Titre de l'application
st.title("Application d'image et de prompt")

# Sélectionner une image
uploaded_image = st.file_uploader("Sélectionnez une image", type=["jpg", "png", "jpeg"])

# Afficher l'image chargée
if uploaded_image is not None:
    tokenizer, model, image_processor, context_len = create_llava_model()

    st.image(uploaded_image, caption="Image chargée", use_column_width=True)

    question = 'Pouvez-vous fournir une description de l\'image en francais?'
    qs = DEFAULT_IMAGE_TOKEN + '\n' + question

    conv = conv_templates['llava_v1'].copy()
    conv.append_message(conv.roles[0], qs)
    conv.append_message(conv.roles[1], None)
    prompt = conv.get_prompt()

    input_ids = tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(0).cuda()

    image = Image.open(uploaded_image)
    image_tensor = image_processor.preprocess(image, return_tensors='pt')['pixel_values'][0]

    stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
    keywords = [stop_str]
    stopping_criteria = KeywordsStoppingCriteria(keywords, tokenizer, input_ids)

    with torch.inference_mode():
        output_ids = model.generate(
            input_ids,
            images=image_tensor.unsqueeze(0).half().cuda(),
            do_sample=True,
            temperature=0.2,
            top_p=None,
            num_beams=1,
            # no_repeat_ngram_size=3,
            max_new_tokens=1024,
            use_cache=True)

    input_token_len = input_ids.shape[1]
    n_diff_input_output = (input_ids != output_ids[:, :input_token_len]).sum().item()
    if n_diff_input_output > 0:
        print(f'[Warning] {n_diff_input_output} output_ids are not the same as the input_ids')
    outputs = tokenizer.batch_decode(output_ids[:, input_token_len:], skip_special_tokens=True)[0]
    outputs = outputs.strip()

    st.write("Description de l'image :")
    st.write(outputs)