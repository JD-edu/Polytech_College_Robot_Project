import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import requests
import json
import os
import io

# --- Configuration ---
API_URL = "http://127.0.0.1:5000/analyze_image"
DEFAULT_IMAGE_PATH = "many_shape3.png" # 기본 이미지 파일 경로

# --- Tkinter UI Setup ---
class ImageAnalysisApp:
    def __init__(self, master):
        self.master = master
        master.title("OpenCV & LLM Image Analysis")
        master.geometry("1200x800") # 초기 창 크기 설정

        # --- Variables ---
        self.original_image = None
        self.annotated_image = None
        self.current_image_path = DEFAULT_IMAGE_PATH

        # --- UI Elements ---

        # 1. Image Frames
        self.image_frame = tk.Frame(master)
        self.image_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.original_image_label = tk.Label(self.image_frame, text="Original Image", compound=tk.TOP, borderwidth=2, relief="groove")
        self.original_image_label.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)

        self.annotated_image_label = tk.Label(self.image_frame, text="Annotated Image (LLM/OpenCV)", compound=tk.TOP, borderwidth=2, relief="groove")
        self.annotated_image_label.pack(side=tk.RIGHT, padx=10, fill=tk.BOTH, expand=True)

        # 2. Buttons Frame
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(pady=10)

        self.load_image_button = tk.Button(self.button_frame, text="이미지 불러오기", command=self.load_image)
        self.load_image_button.pack(side=tk.LEFT, padx=10)

        self.analyze_button = tk.Button(self.button_frame, text="이미지 문의하기", command=self.analyze_image)
        self.analyze_button.pack(side=tk.LEFT, padx=10)

        self.clear_button = tk.Button(self.button_frame, text="모두 클리어", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=10)

        # 3. Text View
        self.text_output_label = tk.Label(master, text="LLM Response:", anchor="w")
        self.text_output_label.pack(padx=20, fill=tk.X)
        self.text_output = scrolledtext.ScrolledText(master, wrap=tk.WORD, height=10, borderwidth=2, relief="groove")
        self.text_output.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Initialize with default image
        self.display_image(DEFAULT_IMAGE_PATH, self.original_image_label, is_original=True)

    def display_image(self, image_path, label_widget, is_original=False):
        """Displays an image in the specified label, resizing it to fit."""
        if not os.path.exists(image_path):
            messagebox.showerror("Error", f"Image file not found at: {image_path}")
            return

        try:
            img = Image.open(image_path)
            
            # Get the current size of the label to fit the image
            label_width = label_widget.winfo_width()
            label_height = label_widget.winfo_height()

            # Ensure label has a size (it might be 0,0 at initial startup)
            if label_width == 1 or label_height == 1: # Default tkinter size if not yet rendered
                label_width = self.master.winfo_width() // 2 - 20 # Estimate half window width
                label_height = int(self.master.winfo_height() * 0.6) # Estimate 60% of window height

            # Resize image to fit label while maintaining aspect ratio
            img.thumbnail((label_width, label_height), Image.Resampling.LANCZOS)
            
            tk_img = ImageTk.PhotoImage(img)
            label_widget.config(image=tk_img)
            label_widget.image = tk_img # Keep a reference!
            
            if is_original:
                self.original_image = tk_img # Store original image reference
            else:
                self.annotated_image = tk_img # Store annotated image reference

        except Exception as e:
            messagebox.showerror("Image Error", f"Could not display image: {e}")

    def load_image(self):
        """Opens a file dialog to select an image and displays it."""
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            self.current_image_path = file_path
            self.display_image(self.current_image_path, self.original_image_label, is_original=True)
            self.clear_output_views() # Clear previous analysis when loading new image
            messagebox.showinfo("Image Loaded", f"'{os.path.basename(file_path)}' 이미지를 불러왔습니다.")

    def analyze_image(self):
        """Sends the current image to the Flask agent for analysis."""
        if not self.current_image_path or not os.path.exists(self.current_image_path):
            messagebox.showerror("Error", "분석할 이미지를 먼저 선택해주세요.")
            return
        
        self.text_output.delete(1.0, tk.END) # Clear previous text output
        self.text_output.insert(tk.END, "AI 에이전트에 문의 중...\n")
        self.text_output.config(fg="gray")
        self.master.update_idletasks() # Update UI to show message

        try:
            with open(self.current_image_path, 'rb') as img_file:
                files = {
                    'image': (os.path.basename(self.current_image_path), img_file, 'image/png')
                }
                data = {
                    'prompt': TEXT_PROMPT
                }

                response = requests.post(API_URL, files=files, data=data)
                response.raise_for_status() # Raise an HTTPError for bad responses

                response_json = response.json()

                # Display annotated image
                annotated_image_url = response_json.get('annotated_image_url')
                if annotated_image_url:
                    # Flask serves files from its root, so we remove leading '/' for local path
                    local_annotated_image_path = annotated_image_url.lstrip('/')
                    if os.path.exists(local_annotated_image_path):
                        self.display_image(local_annotated_image_path, self.annotated_image_label)
                    else:
                        messagebox.showwarning("Image Error", f"주석 처리된 이미지를 찾을 수 없습니다: {local_annotated_image_path}")

                # Display LLM response text
                llm_response_text = "LLM 측정 순서 제안:\n"
                if 'measurement_order_full_json' in response_json and \
                   'measurement_sequence' in response_json['measurement_order_full_json']:
                    
                    for item in response_json['measurement_order_full_json']['measurement_sequence']:
                        llm_response_text += (
                            f"Step {item.get('step', '?')}: "
                            f"Shape ID {item.get('shape_id', '?')} ({item.get('shape_type', 'Unknown Type')}) "
                            f"at ({item.get('center_x_pixel', '?')}, {item.get('center_y_pixel', '?')}) pixels. "
                            f"Reason: {item.get('reason', 'N/A')}\n"
                        )
                    llm_response_text += "\n"
                
                # Add simplified list info
                if 'simplified_measurement_list' in response_json:
                    llm_response_text += "Simplified Measurement List (for motor control):\n"
                    for item in response_json['simplified_measurement_list']:
                        llm_response_text += (
                            f"  - X: {item.get('x', '?')}, Y: {item.get('y', '?')}, Type: {item.get('shape', 'Unknown')}\n"
                        )
                else:
                    llm_response_text += "No measurement sequence or simplified list found.\n"


                self.text_output.delete(1.0, tk.END)
                self.text_output.insert(tk.END, llm_response_text)
                self.text_output.config(fg="black") # Change text color back to black
                
        except requests.exceptions.ConnectionError as e:
            messagebox.showerror("Connection Error", f"Flask 앱에 연결할 수 없습니다. '{API_URL}'에서 실행 중인가요?\nDetails: {e}")
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(tk.END, f"오류: Flask 앱에 연결할 수 없음.\n{e}")
            self.text_output.config(fg="red")
        except requests.exceptions.HTTPError as e:
            messagebox.showerror("HTTP Error", f"HTTP 상태 코드 {response.status_code} 수신.\nDetails: {response.text}")
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(tk.END, f"오류: HTTP 응답 오류.\n{response.text}")
            self.text_output.config(fg="red")
        except json.JSONDecodeError:
            messagebox.showerror("JSON Error", f"JSON 응답 디코딩 실패.\nRaw response: {response.text}")
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(tk.END, f"오류: JSON 응답 디코딩 실패.\n{response.text}")
            self.text_output.config(fg="red")
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"예상치 못한 오류 발생: {e}")
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(tk.END, f"예상치 못한 오류 발생: {e}")
            self.text_output.config(fg="red")

    def clear_output_views(self):
        """Clears the annotated image view and the text output."""
        self.annotated_image_label.config(image='')
        self.annotated_image = None # Release reference
        self.text_output.delete(1.0, tk.END)

    def clear_all(self):
        """Clears all views (original image, annotated image, and text output)."""
        self.original_image_label.config(image='')
        self.original_image = None # Release reference
        self.clear_output_views()
        messagebox.showinfo("Clear", "모든 화면이 초기화되었습니다.")


# --- Run the application ---
if __name__ == "__main__":
    # Ensure PIL (Pillow) is installed: pip install Pillow
    # Ensure requests is installed: pip install requests
    
    # Check if default image exists
    if not os.path.exists(DEFAULT_IMAGE_PATH):
        print(f"Warning: Default image '{DEFAULT_IMAGE_PATH}' not found.")
        print("Please place 'many_shape3.png' in the same directory or load an image manually.")
        
    root = tk.Tk()
    app = ImageAnalysisApp(root)
    root.mainloop()