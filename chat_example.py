import streamlit as st
from streamlit_chat import message
import requests

import os
import azure.cognitiveservices.speech as speechsdk

import openai
import azure.cognitiveservices.speech as speechsdk
from googletrans import Translator


openai.api_key = st.secrets["openai"]
subscription = st.secrets["subscription"]
region='eastus'

st.set_page_config(
    page_title="Streamlit Chat - Demo",
    page_icon=":robot:"
)

st.header("Streamlit Chat - Demo")
st.markdown("[Github](https://github.com/ai-yash/st-chat)")

if 'generated' not in st.session_state:
    st.session_state["generated"] = ["Tá sé go hiontach tú a fheiceáil, tá súil agam go bhfuil do theaghlach go maith."]

if 'past' not in st.session_state:
    st.session_state['past'] = ["Dia duit, tá sé iontach tú a fheiceáil."]

st.session_state['prompt'] = """
Seo a leanas comhrá le cara. Tá an cara cabhrach, cruthaitheach, cliste, agus an-chairdiúil.

Tusa: Dia duit, tá sé iontach tú a fheiceáil.
Cara: Tá sé go hiontach tú a fheiceáil, tá súil agam go bhfuil do theaghlach go maith.
Tusa:
"""

def recognize_from_microphone():
    speech_config = speechsdk.SpeechConfig(subscription=subscription, region='eastus')
    speech_config.speech_recognition_language="ga-IE"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(speech_recognition_result.text))
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
            
    return speech_recognition_result.text

def get_gtp(prompt):
    response = openai.Completion.create(
      model="text-davinci-002",
      prompt=prompt,
      temperature=0.5,
      max_tokens=60,
      top_p=1.0,
      frequency_penalty=0.5,
      presence_penalty=0.0,
      stop=["Tusa:"]
)
    return response

def translate(text):
    translator = Translator() 
    translate_text = translator.translate(text, dest='ga')
    return translate_text.text


def ai_speak(text, subscription, region):
    speech_config = speechsdk.SpeechConfig(subscription, region)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

    # The language of the voice that speaks.
    speech_config.speech_synthesis_voice_name='ga-IE-OrlaNeural'

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    # Get text from the console and synthesize to the default speaker.
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("AI: [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")

placeholder = st.empty()
user_input = False

if st.button('Reply'):
    user_input = recognize_from_microphone()
    user_input = user_input.strip()
    prompt = st.session_state['prompt'].strip() + user_input + '\nCara:'
    response = get_gtp(prompt)
    response_text = response['choices'][0]['text']
    response_text = translate(response_text)
    ai_speak(response_text, subscription, region)

    st.session_state.past.append(user_input)
    st.session_state.generated.append(response_text)
    prompt = prompt.strip() + response_text + '\nTusa:'
    st.session_state['prompt'] = prompt

if st.session_state['generated']:
    with placeholder.container():
        for i in range(0, len(st.session_state['generated']), 1):
            message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))
