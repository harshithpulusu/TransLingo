import tkinter as tk
from tkinter import ttk, messagebox
from googletrans import Translator
import speech_recognition as sr
import pyttsx3
import threading

class LanguageTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Easy Language Translator")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        self.translator = Translator()
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()

        # Source language input
        ttk.Label(root, text="Source Language Code (e.g., en):").pack(pady=5)
        self.src_lang = ttk.Entry(root, width=10)
        self.src_lang.pack()

        # Destination language input
        ttk.Label(root, text="Destination Language Code (e.g., fr):").pack(pady=5)
        self.dest_lang = ttk.Entry(root, width=10)
        self.dest_lang.pack()

        # Text input
        ttk.Label(root, text="Text to Translate:").pack(pady=5)
        self.text_input = tk.Text(root, height=5, width=50)
        self.text_input.pack()

        # Button frame
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=5)
        
        # Translate button
        ttk.Button(button_frame, text="Translate", command=self.translate_text).pack(side=tk.LEFT, padx=5) # Translate button
        
        # Voice input button
        ttk.Button(button_frame, text="Voice Input", command=self.voice_input).pack(side=tk.LEFT, padx=5)
        
        # Speak translation button
        ttk.Button(button_frame, text="Speak Translation", command=self.speak_translation).pack(side=tk.LEFT, padx=5)

        # Output
        ttk.Label(root, text="Translated Text:").pack(pady=5)
        self.output_text = tk.Text(root, height=5, width=50, state="disabled")
        self.output_text.pack()

    def translate_text(self):
        src = self.src_lang.get().strip()
        dest = self.dest_lang.get().strip()
        text = self.text_input.get("1.0", tk.END).strip()

        if not src or not dest or not text:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            translated = self.translator.translate(text, src=src, dest=dest)
            self.output_text.config(state="normal")
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, translated.text)
            self.output_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Translation Error", str(e))

    def voice_input(self):
        """Capture voice input and convert to text"""
        try:
            messagebox.showinfo("Voice Input", "Speak now...")
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", text)
        except sr.WaitTimeoutError:
            messagebox.showerror("Error", "No speech detected within timeout")
        except sr.RequestError:
            messagebox.showerror("Error", "Could not request results from speech recognition service")
        except sr.UnknownValueError:
            messagebox.showerror("Error", "Could not understand the audio")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def speak_translation(self):
        """Read the translated text aloud"""
        text = self.output_text.get("1.0", tk.END).strip()
        if text:
            try:
                def speak():
                    self.engine.say(text)
                    self.engine.runAndWait()
                
                # Run in a separate thread to prevent GUI freezing
                threading.Thread(target=speak, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Error", f"Could not speak the text: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No text to speak")


if __name__ == "__main__":
    root = tk.Tk()
    app = LanguageTranslatorApp(root)
    root.mainloop()
