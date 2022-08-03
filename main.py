
import time
from azure.cognitiveservices.speech.audio import AudioOutputConfig
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient,RecognizeEntitiesAction,RecognizeLinkedEntitiesAction,ExtractKeyPhrasesAction
from azure.storage.blob import ContainerClient
import json
import tkinter
from tkinter import filedialog
import os
import azure.cognitiveservices.speech as speech_sdk
from pdf2image import convert_from_path


def search_for_file_path ():
    currdir = os.getcwd()
    tempdir = filedialog.askdirectory(parent=root, initialdir=currdir, title='Please select a directory')
    if len(tempdir) > 0:
        print ("You chose: %s" % tempdir)
    return tempdir

def search_for_PDF ():
    currdir = os.getcwd()
    tempdir = filedialog.askopenfilename(parent=root, initialdir=currdir, title='Please select a directory')
    if len(tempdir) > 0:
        print ("You chose: %s" % tempdir)
    return tempdir

if __name__ == '__main__':
    root = tkinter.Tk()
    root.withdraw()

    Local_pdf = search_for_PDF()
    if (Local_pdf):
        output = search_for_file_path()
        if (output):

            Number_of_pages = 0;


            def convert_pdf_to_images(pdf_path, output): #to extract images of a pdf
                images = convert_from_path(pdf_path)
                file_name = (os.path.split(Local_pdf)[1])
                filename_wout_ext = file_name.split('.')[0]
                for index, image in enumerate(images):
                    output_string = f'{output}/{filename_wout_ext}{index}.png'
                    image.save(output_string)
                    global Number_of_pages
                    Number_of_pages = index
                return filename_wout_ext

            credential = json.load(open('credential.json'))
            API_KEY_vision = credential['API_KEY_vision']
            ENDPOINT_vision = credential['ENDPOINT_vision']
            API_KEY_speech = credential['API_KEY_speech']
            ENDPOINT_speech = credential['ENDPOINT_speech']
            API_KEY_Language = credential['API_KEY_Language']
            ENDPOINT_Language = credential['ENDPOINT_Language']
            speech_region = credential['region']
            connection_string = credential['connection_string']
            container_name = credential['container_name']

            cv_client = ComputerVisionClient(ENDPOINT_vision, CognitiveServicesCredentials(API_KEY_vision))
            text_analytics_client = TextAnalyticsClient(endpoint=ENDPOINT_Language, credential=AzureKeyCredential(API_KEY_Language))

            Local_pdf = Local_pdf
            filename_wout_ext=convert_pdf_to_images(Local_pdf, output)
            output_text = open(f'{output}/{filename_wout_ext}.txt', "w+")
            file_name=(os.path.split(Local_pdf)[1])



            for Num in range(Number_of_pages + 1):
                image_address = f'{output}/{filename_wout_ext}' + str(Num) + '.png'
                rawHttpResponse = cv_client.read_in_stream(open(image_address, 'rb'), Language='en', raw=True)
                operationLocation = rawHttpResponse.headers["Operation-Location"]
                operationId = operationLocation.split('/')[-1]
                time.sleep(2)
                Result = cv_client.get_read_result(operationId)

                if Result.status == OperationStatusCodes.succeeded:
                    for line in Result.analyze_result.read_results[0].lines:
                        output_text.write(' ' + line.text)


                else:
                    print(Result.status)

            output_text.close() # end of text extraction ******************


            output_text = open(f'{output}/{filename_wout_ext}.txt', "r")
            output_extra_info_in_text=open(f'{output}/{filename_wout_ext}_anlyze.txt', "w+")
            string = output_text.read()
            documents = [string]


#start of the text analysis using multiple action option
            poller = text_analytics_client.begin_analyze_actions(
                documents,
                display_name="Sample Text Analysis",
                actions=[
                    RecognizeEntitiesAction(),
                    RecognizeLinkedEntitiesAction(),
                    ExtractKeyPhrasesAction(),

                ]
            )

            #
            document_results = poller.result()
            for doc, action_results in zip(documents, document_results):
                recognize_entities_result, recognize_linked_entities_result,Extract_KeyPhrases_result = action_results


                output_extra_info_in_text.write("Results of Recognize Entities Action:\n\n")
                if recognize_entities_result.is_error:
                    print(f"Is an error with code '{recognize_entities_result.code}' "
                          f"and message '{recognize_entities_result.message}'")
                else:
                    for entity in recognize_entities_result.entities:
                        output_extra_info_in_text.write(f"Entity: {entity.text}\n\n")
                        output_extra_info_in_text.write(f"Category: {entity.category}\n\n")
                        output_extra_info_in_text.write(f"Confidence Score: {entity.confidence_score}\n\n")
                        output_extra_info_in_text.write(f"Offset: {entity.offset}\n\n")



                output_extra_info_in_text.write("\n\n Results of Recognize linked Entities Action:\n\n")
                if recognize_linked_entities_result.is_error:
                    print(f"Is an error with code '{recognize_linked_entities_result.code}' "
                          f"and message '{recognize_linked_entities_result.message}'")
                else:
                    for entity in recognize_linked_entities_result.entities:
                        output_extra_info_in_text.write(f"Entity: {entity.name}\n\n")
                        output_extra_info_in_text.write(f"URL: {entity.url}\n\n")
                        output_extra_info_in_text.write(f"Data Source: {entity.data_source}\n\n")
                        output_extra_info_in_text.write("Entity matches:\n\n")
                        for match in entity.matches:
                            output_extra_info_in_text.write(f"Entity match text: {match.text}\n\n")
                            output_extra_info_in_text.write(f"Confidence Score: {match.confidence_score}\n\n")
                            output_extra_info_in_text.write(f"Offset: {match.offset}\n\n")


                output_extra_info_in_text.write("\n\nResults of Extract_KeyPhrases_result Action:\n\n")
                if Extract_KeyPhrases_result.is_error:
                    print(f"Is an error with code '{Extract_KeyPhrases_result.code}' "
                          f"and message '{Extract_KeyPhrases_result.message}'")
                else:

                        output_extra_info_in_text.write("Key Phrases: {}\n\n".format(Extract_KeyPhrases_result.key_phrases))

                output_extra_info_in_text.write("------------------------------------------")

            # end of the text analysis


            output_extra_info_in_text.close()
            config = speech_sdk.SpeechConfig(subscription=API_KEY_speech, region=speech_region)
            synthesizer = speech_sdk.SpeechSynthesizer(speech_config=config)
            output_sound_file =f'{output}/{filename_wout_ext}.mp3'
            audio_config = AudioOutputConfig(
                filename=output_sound_file)

            synthesizer = speech_sdk.SpeechSynthesizer(speech_config=config, audio_config=audio_config)
            speech_synthesis_result = synthesizer.speak_text_async(string).get()


            if speech_synthesis_result.reason == speech_sdk.ResultReason.SynthesizingAudioCompleted:
                print("Speech synthesized finished successfully ")

                container_client=ContainerClient.from_connection_string(connection_string,container_name)
                blob_client=container_client.get_blob_client(filename_wout_ext)
                with open(output_sound_file ,"rb") as data:
                    blob_client.upload_blob(data,overwrite=True)



            elif speech_synthesis_result.reason == speech_sdk.ResultReason.Canceled:
                cancellation_details = speech_synthesis_result.cancellation_details
                print("Speech synthesis canceled: {}".format(cancellation_details.reason))

                if cancellation_details.reason == speech_sdk.CancellationReason.Error:

                    if cancellation_details.error_details:
                        print("Error details: {}".format(cancellation_details.error_details))
                        print("Did you set the speech resource key and region values?")





