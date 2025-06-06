# source ~/Desktop/robot-env/bin/activate
# cd Desktop

# ros2 launch rosbridge_server rosbridge_websocket_launch.xml

import tkinter as tk
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
import numpy as np
from scipy.io.wavfile import read
import roslibpy # type: ignore

is_recording = False
recording_stream = None
audio_data = []
#nlp = spacy.load("en_core_web_sm")

def beep(frequency=440, duration=0.2, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(frequency * 2 * np.pi * t)
    audio = tone.astype(np.float32)
    sd.play(audio, sample_rate)
    sd.wait()


def subscribe_func(msg):
    feedback = msg['data']
    if (feedback == "success"):
        beep(duration=1)
    elif (feedback == "failure"):
        beep(frequency=300, duration=1)

try:
    # Connect to ROS bridge (change 'localhost' to the robot's IP if remote)
    client = roslibpy.Ros(host='rocky.hcrlab.cs.washington.edu', port=9090)
    client.run()

    # Define the ROS topic and message format
    command_topic = roslibpy.Topic(client, '/team3voicecommand', 'std_msgs/String')
    feedback_topic = roslibpy.Topic(client, '/team3voicefeedback', 'std_msgs/String')

    command_topic.advertise()
    feedback_topic.subscribe(subscribe_func)
except Exception as e:
    print("Failed to connect to ROS")





def record_audio():
    global is_recording, recording_stream, audio_data

    if not is_recording:
        print("Beep: start recording")
        beep()
        
        print("Recording started... Press again to stop.")
        is_recording = True
        audio_data = []

        # Start a non-blocking stream
        def callback(indata, frames, time, status):
            if status:
                print("Recording error:", status)
            audio_data.append(indata.copy())

        recording_stream = sd.InputStream(samplerate=44100, channels=1, callback=callback)
        recording_stream.start()

        # Update button label
        record_button.config(text="Stop Recording")

    else:
        print("Beep: end recording")
        beep(frequency=300)
        print("Recording stopped.")
        is_recording = False

        recording_stream.stop()
        recording_stream.close()

        # Concatenate and save
        full_audio = np.concatenate(audio_data, axis=0)
        audio_int16 = (full_audio * 32767).astype('int16')
        write('audio.wav', 44100, audio_int16)

        print("Audio saved as audio.wav")

        # Reset button label
        record_button.config(text="Record Audio Description")


def play_audio():
    try:
        fs, data = read('audio.wav')
        # Normalize if it's int16 format
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32767
        sd.play(data, fs)
        sd.wait()
        print("Playback finished.")
    except Exception as e:
        print("Error during playback:", e)


def send_request():
    print("Sending processed request to robot...")

    recognizer = sr.Recognizer()
    audio_file = "audio.wav"

    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            print("Transcribed Text:", text)

            text_array = text.lower().split(" ")
            print(text_array)
            possible_objects = ["bowl", "spoon", "fork", "knife", "cup"]
            object_to_grab = None
            for obj in possible_objects:
                if obj in text_array:
                    object_to_grab = obj
                    break
            print(object_to_grab)
            if (object_to_grab is not None):
                send_to_ros("", object_to_grab)
                beep(frequency=800)
            # doc = nlp(text)

            # print(doc)

            # grabbed_objects = []

            # for token in doc:
            #     # Focus only on the verb "grab" or "grabs"
            #     if token.lemma_ == "grab" and token.pos_ == "VERB":
            #         for child in token.children:
            #             if child.dep_ in ("dobj", "attr", "pobj") and child.pos_ == "NOUN":
            #                 noun = child.text.lower()
            #                 grabbed_objects.append(noun)

            # print("Objects to grab:", grabbed_objects)

            # with open("parsed_keywords.txt", "w") as f:
            #     f.write("Grabbed Objects: " + ", ".join(grabbed_objects) + "\n")

            # if grabbed_objects:
            #     for obj in grabbed_objects:
            #         send_to_ros("grab", obj)
            # else:
            #     print("No valid grab target found.")

    except sr.UnknownValueError:
        print("Could not understand the audio.")
    except sr.RequestError as e:
        print(f"Speech recognition request failed: {e}")
    except FileNotFoundError:
        print("Audio file not found. Please record first.")

def send_to_ros(verb, noun):
    try:
        # Connect to ROS bridge (change 'localhost' to the robot's IP if remote)
        #client = roslibpy.Ros(host='rocky.hcrlab.cs.washington.edu', port=9090)
        #client.run()

        # Define the ROS topic and message format
        #command_topic = roslibpy.Topic(client, '/team3voicecommand', 'std_msgs/String')
        
        #command_topic.advertise()

        # Combine verb and noun into a simple string command
        #command = f'{verb} {noun}'  # e.g., 'grab cup'
        command = noun  # e.g., 'grab cup'
        command_topic.publish(roslibpy.Message({'data': command}))
        print('Sent to robot:', command)

        # Clean up connection
        #command_topic.unadvertise()
        #client.terminate()

    except Exception as e:
        print('Failed to send command to robot:', e)


# Create the main window
root = tk.Tk()
root.title("Assistive Robot UI")
root.attributes('-fullscreen', True)
root.configure(bg="white")

#container = tk.Frame(root, bg="white")
#container.pack(expand=True)
#container.place(relx=0.5, rely=0.5, anchor='center')

button_font = ("Arial", 28, "bold")

# Buttons
record_button = tk.Button(root, text="Record Audio Description", command=record_audio,
                          font=button_font, bg="lightblue")
record_button.pack(fill='both', expand=True)

play_button = tk.Button(root, text="Play Back Recording", command=play_audio,
                        font=button_font, bg="lightyellow")
play_button.pack(fill='both', expand=True)

send_button = tk.Button(root, text="Send Request to Robot", command=send_request,
                        font=button_font, bg="lightgreen")
send_button.pack(fill='both', expand=True)


def keyPress(event):
    if event.char == "f":
        print("f is pressed")
        play_audio()
    if event.char == "j":
        print("j is pressed")
        send_request()
def spacePress(event):
    print("space is pressed")
    record_audio()

root.bind("<KeyPress>",keyPress)
root.bind("<space>",spacePress)

# Start the GUI loop
root.mainloop()