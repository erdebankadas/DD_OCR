import base64
import json
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from datetime import datetime
import re


MODEL = "gpt-4o-mini"
# ====================

json_cache = None  # Can store dict or string

def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        messagebox.showerror("Error", f"Image file not found:\n{image_path}")
        return None

def clean_json_text(text):
    """Remove code block markers like ```json ... ```"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    return text

def extract_json_from_image(image_path):
    image_b64 = image_to_base64(image_path)
    if not image_b64:
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an OCR and data extraction expert. Return ONLY a valid JSON object with clean key-value pairs."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all fields from this image and return JSON only."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        "temperature": 0
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, json=payload)
        resp_json = response.json()
    except Exception as e:
        messagebox.showerror("Error", f"API Request Failed:\n{e}")
        return None

    if "error" in resp_json:
        messagebox.showerror("API Error", resp_json["error"]["message"])
        return None

    try:
        result_text = resp_json["choices"][0]["message"]["content"]
        cleaned_text = clean_json_text(result_text)

        # Try parsing JSON
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            return cleaned_text  # Store as string if not valid JSON

    except Exception as e:
        messagebox.showerror("Error", f"Unexpected API Response:\n{e}")
        return None

def select_file():
    filepath = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
    )
    if filepath:
        file_path_var.set(filepath)

def run_extraction():
    global json_cache
    path = file_path_var.get()
    if not path:
        messagebox.showwarning("Warning", "Please select an image file first.")
        return

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "Processing...\n")
    window.update()

    json_result = extract_json_from_image(path)
    if json_result:
        json_cache = json_result
        # Directly show in output_text
        if isinstance(json_cache, dict):
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, json.dumps(json_cache, indent=4, ensure_ascii=False))
        else:
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, str(json_cache))
    else:
        messagebox.showinfo("Info", "No JSON extracted.")

def download_json():
    """Save the last extracted JSON to a file with current date & time."""
    if not json_cache:
        messagebox.showwarning("Warning", "No JSON data to download.")
        return

    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.json")
    filepath = filedialog.asksaveasfilename(
        initialfile=filename,
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json")]
    )

    if filepath:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                if isinstance(json_cache, dict):
                    json.dump(json_cache, f, indent=4, ensure_ascii=False)
                else:
                    f.write(str(json_cache))
            messagebox.showinfo("Success", f"JSON saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save JSON:\n{e}")

# ====== GUI ======
window = tk.Tk()
window.title("OCR JSON Extractor")
window.geometry("700x550")

file_path_var = tk.StringVar()

tk.Label(window, text="Selected Image:").pack(pady=5)
tk.Entry(window, textvariable=file_path_var, width=60).pack(pady=5)

btn_frame = tk.Frame(window)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Browse Image", command=select_file, width=15).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Extract JSON", command=run_extraction, width=15).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Download JSON", command=download_json, width=15).grid(row=0, column=2, padx=5)

# Added Exit button
tk.Button(btn_frame, text="Exit", command=window.destroy, width=15).grid(row=0, column=3, padx=5)

output_text = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=80, height=20)
output_text.pack(pady=10, fill=tk.BOTH, expand=True)

window.mainloop()
