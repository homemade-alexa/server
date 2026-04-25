import azure.cognitiveservices.speech as speechsdk
import logging

SPEECH_KEY = '8390cea6edea4ef1989434e228092efc'
SPEECH_REGION = 'westeurope'

logger = logging.getLogger(__name__)

class SpeechToText:
    @staticmethod
    def recognize(filename: str) -> str:
        try:
            speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
            speech_config.speech_recognition_language = "pl-PL"

            audio_config = speechsdk.audio.AudioConfig(filename=filename)
            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

            speech_recognition_result = speech_recognizer.recognize_once_async().get()

            if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return speech_recognition_result.text
            elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
                logger.info("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
            elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speech_recognition_result.cancellation_details
                logger.info("Speech Recognition canceled: {}".format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.error("Error details: {}".format(cancellation_details.error_details))
                    logger.error("Did you set the speech resource key and region values?")
        except Exception as e:
            logger.error(e)

        return ''
