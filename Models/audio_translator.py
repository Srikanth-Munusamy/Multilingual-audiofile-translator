from transformers import WhisperProcessor, WhisperForConditionalGeneration
from gtts import gTTS
import torchaudio
import logging
import os
import requests
from pydub import AudioSegment
import subprocess
import time
import librosa
import torch
#import customtkinter
import httpx
#from CTkMenuBar import *  # Addon Downloaded from https://github.com/Akascape/CTkMenuBar
import re
#from tkinter import StringVar
import pygame
from .sentence_translator import SentenceTranslator

class CustomTranslator:
    def __init__(self):
        self.processor = None
        self.model = None
        self.target_language = "en"  # Default target language
        self.input_audio_text = ""
        self.translated_text = ""


    def load_model(self):
        # Load the model if it hasn't been loaded
        if self.processor is None:
            self.processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2")

        if self.model is None:
            self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v2")

        # Move the model to GPU if available
        if torch.cuda.is_available():
            self.model.to('cuda')

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(device)

    def unload_model(self):
        # Unload the model if it has been loaded
        if self.processor is not None:
            del self.processor
            self.processor = None

        if self.model is not None:
            # Move the model back to CPU before deleting
            if torch.cuda.is_available():
                self.model.to('cpu')
            del self.model
            self.model = None

    def process_audio(self, input_path, target_language, output_path):
        try:
            self.load_model()

            # Load the full input audio file
            input_waveform, input_sampling_rate = librosa.load(input_path, sr=None, mono=True)

            # Split audio into smaller chunks of ~30 seconds each
            chunk_duration = 30  # in seconds
            total_duration = librosa.get_duration(y=input_waveform, sr=input_sampling_rate)
            chunk_size = chunk_duration * input_sampling_rate

            all_translations = []
            for i in range(0, len(input_waveform), chunk_size):
                chunk = input_waveform[i:i + chunk_size]
                if len(chunk) == 0:
                    break

                # Resample to 16kHz if needed
                if input_sampling_rate != 16000:
                    resampler = torchaudio.transforms.Resample(orig_freq=input_sampling_rate, new_freq=16000)
                    chunk = resampler(torch.tensor(chunk)).numpy()

                # Process audio chunk
                input_features = self.processor(chunk, sampling_rate=16000, return_tensors="pt")
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                input_features = input_features.to(device)

                # Generate transcription
                forced_decoder_ids = self.processor.get_decoder_prompt_ids(language=target_language, task="translate")
                predicted_ids = self.model.generate(input_features["input_features"], forced_decoder_ids=forced_decoder_ids)
                transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

                # Clean duplicate words
                words = transcription.split()
                cleaned_transcription = ' '.join([words[0]] + [word for j, word in enumerate(words[1:]) if word != words[j]])

                # Translate chunk if target language is not English
                if target_language != "en":
                    translator = SentenceTranslator(src="en", dst=target_language)
                    translated_text = translator(cleaned_transcription)
                    all_translations.append(translated_text)
                else:
                    all_translations.append(cleaned_transcription)

            # Combine all translated chunks into a single text
            final_translation = ' '.join(all_translations)

            # Generate a single MP3 file with the final translated text
            self.generate_audio(final_translation, output_path, target_language)

            return final_translation

        except Exception as e:
            logging.error(f"Error processing audio: {e}")
            raise
        finally:
            self.unload_model()



    def get_input_audio_text(self):
        return self.input_audio_text

    def get_translated_text(self):
        return self.translated_text

    def generate_audio(self, text, output_path, target_language):
        tts = gTTS(text, lang=target_language, slow=False)
        tts.save(output_path)

    def play_audio(self, audio_path): # disabled for now
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()

    def stop_audio(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        try:
            pygame.mixer.music.stop()
        except:
            pass
