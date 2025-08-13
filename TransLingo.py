#python -m pip install deep-translator SpeechRecognition
#python Translater.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
import threading
import speech_recognition as sr
from deep_translator import GoogleTranslator
import requests  # For HTTP requests
import subprocess  # For macOS text-to-speech command

class EnhancedLanguageTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TransLingo - AI-Powered Language Translator")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # Initialize components
        self.translator = GoogleTranslator()
        self.speech_recognizer = sr.Recognizer()
        self.tts_engine = None  # We'll use system say command
        self.translation_history = []
        self.load_history()
        
        self.setup_ui()

    def setup_ui(self):
        # Main frame with tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Translation tab
        self.translation_frame = ttk.Frame(notebook)
        notebook.add(self.translation_frame, text="Translation")
        self.setup_translation_tab()

        # History tab
        self.history_frame = ttk.Frame(notebook)
        notebook.add(self.history_frame, text="History")
        self.setup_history_tab()

        # Settings tab
        self.settings_frame = ttk.Frame(notebook)
        notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()

    def setup_translation_tab(self):
        # Language selection with dropdown
        lang_frame = ttk.Frame(self.translation_frame)
        lang_frame.pack(pady=10, fill="x")

        # Get the list of supported languages
        languages = GoogleTranslator().get_supported_languages()
        
        ttk.Label(lang_frame, text="From:").grid(row=0, column=0, padx=5)
        self.src_lang_var = tk.StringVar(value="auto")
        self.src_lang_combo = ttk.Combobox(lang_frame, textvariable=self.src_lang_var, width=15)
        self.src_lang_combo['values'] = ["auto"] + languages
        self.src_lang_combo.grid(row=0, column=1, padx=5)

        # Swap button
        ttk.Button(lang_frame, text="⇄", command=self.swap_languages, width=3).grid(row=0, column=2, padx=5)

        ttk.Label(lang_frame, text="To:").grid(row=0, column=3, padx=5)
        self.dest_lang_var = tk.StringVar(value="spanish")
        self.dest_lang_combo = ttk.Combobox(lang_frame, textvariable=self.dest_lang_var, width=15)
        self.dest_lang_combo['values'] = languages
        self.dest_lang_combo.grid(row=0, column=4, padx=5)

        # Input section with speech recognition
        input_frame = ttk.LabelFrame(self.translation_frame, text="Input Text")
        input_frame.pack(pady=10, fill="both", expand=True)

        # Input controls
        input_controls = ttk.Frame(input_frame)
        input_controls.pack(fill="x", padx=5, pady=5)

        ttk.Button(input_controls, text="🎤 Voice Input", command=self.voice_input).pack(side="left", padx=5)
        ttk.Button(input_controls, text="📁 Load File", command=self.load_file).pack(side="left", padx=5)
        ttk.Button(input_controls, text="🗑️ Clear", command=self.clear_input).pack(side="left", padx=5)

        # Text input with character count
        self.text_input = tk.Text(input_frame, height=6, wrap="word")
        input_scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.text_input.yview)
        self.text_input.configure(yscrollcommand=input_scrollbar.set)
        self.text_input.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        input_scrollbar.pack(side="right", fill="y", pady=5)

        self.char_count_label = ttk.Label(input_frame, text="Characters: 0")
        self.char_count_label.pack(anchor="e", padx=5)
        self.text_input.bind("<KeyRelease>", self.update_char_count)

        # Translate button with loading indicator
        self.translate_btn = ttk.Button(self.translation_frame, text="🔄 Translate", command=self.translate_text_threaded)
        self.translate_btn.pack(pady=10)

        self.progress_bar = ttk.Progressbar(self.translation_frame, mode='indeterminate')
        self.progress_bar.pack(pady=5, fill="x")

        # Output section
        output_frame = ttk.LabelFrame(self.translation_frame, text="Translation Result")
        output_frame.pack(pady=10, fill="both", expand=True)

        # Output controls
        output_controls = ttk.Frame(output_frame)
        output_controls.pack(fill="x", padx=5, pady=5)

        ttk.Button(output_controls, text="🔊 Speak", command=self.speak_translation).pack(side="left", padx=5)
        ttk.Button(output_controls, text="📋 Copy", command=self.copy_translation).pack(side="left", padx=5)
        ttk.Button(output_controls, text="💾 Save", command=self.save_translation).pack(side="left", padx=5)

        # Translation output with confidence score
        self.output_text = tk.Text(output_frame, height=6, wrap="word", state="disabled")
        output_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scrollbar.set)
        self.output_text.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        output_scrollbar.pack(side="right", fill="y", pady=5)

        # Additional info (sentiment, confidence)
        self.info_label = ttk.Label(output_frame, text="")
        self.info_label.pack(anchor="w", padx=5)

    def setup_history_tab(self):
        # History list with search
        search_frame = ttk.Frame(self.history_frame)
        search_frame.pack(pady=10, fill="x")

        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<KeyRelease>", self.filter_history)

        ttk.Button(search_frame, text="Clear History", command=self.clear_history).pack(side="right", padx=5)

        # History listbox
        history_list_frame = ttk.Frame(self.history_frame)
        history_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.history_listbox = tk.Listbox(history_list_frame, height=15)
        history_scrollbar = ttk.Scrollbar(history_list_frame, orient="vertical", command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        self.history_listbox.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")

        self.history_listbox.bind("<Double-1>", self.load_from_history)
        self.update_history_display()

    def setup_settings_tab(self):
        # API Settings
        api_frame = ttk.LabelFrame(self.settings_frame, text="API Settings")
        api_frame.pack(pady=10, fill="x", padx=10)

        ttk.Label(api_frame, text="OpenAI API Key:").pack(anchor="w", padx=5, pady=2)
        self.openai_key_entry = ttk.Entry(api_frame, show="*", width=50)
        self.openai_key_entry.pack(padx=5, pady=2, fill="x")

        # TTS Settings
        tts_frame = ttk.LabelFrame(self.settings_frame, text="Text-to-Speech Settings")
        tts_frame.pack(pady=10, fill="x", padx=10)

        ttk.Label(tts_frame, text="Speech Rate:").pack(anchor="w", padx=5, pady=2)
        self.tts_rate_var = tk.IntVar(value=200)
        ttk.Scale(tts_frame, from_=100, to=300, variable=self.tts_rate_var, orient="horizontal").pack(fill="x", padx=5, pady=2)

        ttk.Label(tts_frame, text="Voice:").pack(anchor="w", padx=5, pady=2)
        import subprocess
        result = subprocess.run(['say', '-v', '?'], capture_output=True, text=True)
        # Parse voice info more carefully
        voices = []
        for line in result.stdout.splitlines():
            if line.strip():
                # Each line format: "name age language region"
                parts = line.strip().split()
                if parts:
                    voices.append(parts[0])  # Take just the voice name
        
        self.voice_var = tk.StringVar(value="")  # Start with system default
        voice_combo = ttk.Combobox(tts_frame, textvariable=self.voice_var)
        voice_combo['values'] = ["System Default"] + voices
        voice_combo.current(0)  # Select "System Default"
        voice_combo.pack(fill="x", padx=5, pady=2)

    def translate_text_threaded(self):
        """Run translation in a separate thread to prevent UI freezing"""
        threading.Thread(target=self.translate_text, daemon=True).start()

    def translate_text(self):
        """Enhanced translation with AI capabilities"""
        self.progress_bar.start()
        self.translate_btn.config(state="disabled")

        try:
            src = self.src_lang_var.get()
            dest = self.dest_lang_var.get()
            text = self.text_input.get("1.0", tk.END).strip()

            if not text:
                messagebox.showerror("Error", "Please enter text to translate.")
                return

            # Basic Google Translate
            translator = GoogleTranslator(source='auto' if src == 'auto' else src,
                                      target=dest)
            translation = translator.translate(text)
            detected_lang = translator.source

            # Update UI in main thread
            self.root.after(0, self.update_translation_result, translation, "", detected_lang)

            # Save to history
            self.add_to_history(text, translation, src, dest)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Translation Error", str(e)))
        finally:
            self.root.after(0, self.translation_complete)

    def update_translation_result(self, translation, sentiment_info, detected_lang):
        """Update the translation result in the UI"""
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, translation)
        self.output_text.config(state="disabled")

        info_text = f"Language: {detected_lang}"
        if sentiment_info:
            info_text += f" | {sentiment_info}"
        self.info_label.config(text=info_text)

    def translation_complete(self):
        """Reset UI after translation is complete"""
        self.progress_bar.stop()
        self.translate_btn.config(state="normal")

    def voice_input(self):
        """Capture voice input using speech recognition"""
        try:
            with sr.Microphone() as source:
                self.speech_recognizer.adjust_for_ambient_noise(source)
                messagebox.showinfo("Voice Input", "Listening... Speak now!")
                audio = self.speech_recognizer.listen(source, timeout=10)
                
            text = self.speech_recognizer.recognize_google(audio)
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", text)
            self.update_char_count()
            
        except sr.UnknownValueError:
            messagebox.showerror("Error", "Could not understand audio")
        except sr.RequestError as e:
            messagebox.showerror("Error", f"Could not request results: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Voice input failed: {e}")

    def speak_translation(self):
        """Speak the translated text using TTS"""
        translation = self.output_text.get("1.0", tk.END).strip()
        if translation:
            threading.Thread(target=self._speak_text, args=(translation,), daemon=True).start()

    def _speak_text(self, text):
        """Internal method to speak text using macOS say command"""
        try:
            import subprocess
            voice = self.voice_var.get()
            if not voice:  # If no voice is selected, use default
                subprocess.run(['say', '-r', str(self.tts_rate_var.get()), text])
            else:
                result = subprocess.run(['say', '-v', voice, '-r', str(self.tts_rate_var.get()), text], 
                                     capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"TTS error: {result.stderr}")
                    # Try without voice specification
                    subprocess.run(['say', '-r', str(self.tts_rate_var.get()), text])
        except Exception as e:
            print(f"TTS error: {e}")
            # Try the simplest possible command as fallback
            try:
                subprocess.run(['say', text])
            except Exception as e2:
                print(f"Fallback TTS error: {e2}")

    def copy_translation(self):
        """Copy translation to clipboard"""
        translation = self.output_text.get("1.0", tk.END).strip()
        if translation:
            self.root.clipboard_clear()
            self.root.clipboard_append(translation)
            messagebox.showinfo("Copied", "Translation copied to clipboard!")

    def save_translation(self):
        """Save translation to file"""
        translation = self.output_text.get("1.0", tk.END).strip()
        if translation:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(translation)
                messagebox.showinfo("Saved", f"Translation saved to {filename}")

    def load_file(self):
        """Load text from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", content)
                self.update_char_count()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def swap_languages(self):
        """Swap source and destination languages"""
        if self.src_lang_var.get() != "auto":
            src = self.src_lang_var.get()
            dest = self.dest_lang_var.get()
            self.src_lang_var.set(dest)
            self.dest_lang_var.set(src)

    def clear_input(self):
        """Clear input text"""
        self.text_input.delete("1.0", tk.END)
        self.update_char_count()

    def update_char_count(self, event=None):
        """Update character count"""
        text = self.text_input.get("1.0", tk.END).strip()
        self.char_count_label.config(text=f"Characters: {len(text)}")

    def add_to_history(self, original, translation, src_lang, dest_lang):
        """Add translation to history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "original": original,
            "translation": translation,
            "src_lang": src_lang,
            "dest_lang": dest_lang
        }
        self.translation_history.insert(0, entry)  # Most recent first
        if len(self.translation_history) > 100:  # Limit history size
            self.translation_history.pop()
        
        self.save_history()
        self.update_history_display()

    def save_history(self):
        """Save translation history to file"""
        try:
            with open("translation_history.json", "w", encoding="utf-8") as f:
                json.dump(self.translation_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

    def load_history(self):
        """Load translation history from file"""
        try:
            if os.path.exists("translation_history.json"):
                with open("translation_history.json", "r", encoding="utf-8") as f:
                    self.translation_history = json.load(f)
        except Exception as e:
            print(f"Failed to load history: {e}")
            self.translation_history = []

    def update_history_display(self):
        """Update history display in the listbox"""
        self.history_listbox.delete(0, tk.END)
        search_term = self.search_var.get().lower()
        
        for i, entry in enumerate(self.translation_history):
            if not search_term or search_term in entry["original"].lower() or search_term in entry["translation"].lower():
                display_text = f"{entry['timestamp'][:16]} | {entry['original'][:50]}... → {entry['translation'][:50]}..."
                self.history_listbox.insert(tk.END, display_text)

    def filter_history(self, event=None):
        """Filter history based on search term"""
        self.update_history_display()

    def load_from_history(self, event):
        """Load selected history item to input"""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            # Find the actual history entry (accounting for filtering)
            search_term = self.search_var.get().lower()
            filtered_entries = []
            for entry in self.translation_history:
                if not search_term or search_term in entry["original"].lower() or search_term in entry["translation"].lower():
                    filtered_entries.append(entry)
            
            if index < len(filtered_entries):
                entry = filtered_entries[index]
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", entry["original"])
                self.src_lang_var.set(entry["src_lang"])
                self.dest_lang_var.set(entry["dest_lang"])
                self.update_char_count()

    def clear_history(self):
        """Clear translation history"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all history?"):
            self.translation_history = []
            self.save_history()
            self.update_history_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedLanguageTranslatorApp(root)
    root.mainloop()