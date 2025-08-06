import cv2
from ultralytics import YOLO
from PIL import Image, ImageTk
import tkinter as tk
from database import init_db, SessionLocal, VehicleRecord

class YOLOModel:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)

    def detect(self, frame):
        results = self.model(frame, imgsz=320, verbose=False)[0]
        return results

class VideoStream:
    def __init__(self, rtsp_url):
        self.cap = cv2.VideoCapture(rtsp_url)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):
        for _ in range(4):
            self.cap.grab()
        ret, frame = self.cap.read()
        return ret, frame

    def release(self):
        self.cap.release()

class TrafficMonitorApp:
    def __init__(self, root, model, video_stream):
        self.root = root
        self.model = model
        self.video_stream = video_stream

        self.setup_gui()
        self.update_frame()

    def setup_gui(self):
        self.root.title("Smart Traffic Monitor")
        self.root.geometry("720x600")
        self.root.configure(bg="white")

        # --- top frame: traffic light + vehicle count ---
        top_frame = tk.Frame(self.root, bg="white")
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        traffic_img = Image.open("traffic_light.png").resize((80, 100))
        self.traffic_icon = ImageTk.PhotoImage(traffic_img)

        self.traffic_label = tk.Label(top_frame, image=self.traffic_icon, bg="white")
        self.traffic_label.pack(side="left", padx=20)

        self.vehicle_text = tk.StringVar()
        self.vehicle_text.set("Vehicles: 0")
        self.vehicle_label = tk.Label(top_frame, textvariable=self.vehicle_text, font=("Arial", 18), fg="black", bg="white")
        self.vehicle_label.pack(side="left", padx=10)

        # --- video label ---
        self.video_label = tk.Label(self.root)
        self.video_label.pack(pady=10)

        # --- control buttons ---
        button_frame = tk.Frame(self.root, bg="white")
        button_frame.pack(side=tk.BOTTOM, pady=20)

        self.red_button = tk.Button(button_frame, text="قرمز", state="disabled", font=("Arial", 14), width=10, bg="#f82323", fg="white")
        self.red_button.grid(row=0, column=0, padx=10)

        self.yellow_button = tk.Button(button_frame, text="زرد", state="disabled", font=("Arial", 14), width=10, bg="#edf100", fg="black")
        self.yellow_button.grid(row=0, column=1, padx=10)

        self.green_button = tk.Button(button_frame, text="سبز", state="disabled", font=("Arial", 14), width=10, bg="#06D606", fg="white")
        self.green_button.grid(row=0, column=2, padx=10)


    def update_frame(self):
        ret, frame =self.video_stream.read()
        if not ret:
            self.root.after(100, self.update_frame)
            return
        
        results = self.model.detect(frame)
        vehicle_counter = 0

        for box in results.boxes:
            cls = int(box.cls)
            if cls in [2, 3, 5, 7]:
                vehicle_counter += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, self.model.model.names[cls], (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        self.vehicle_text.set(f"Vehicles: {vehicle_counter}") 

        # save in data base
        try:
            session = SessionLocal()
            session.add(VehicleRecord(count=vehicle_counter))
            session.commit()
        finally:
            session.close()
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized_frame = cv2.resize(rgb_frame, (640, 360))
        img = Image.fromarray(resized_frame)
        imgtk = ImageTk.PhotoImage(image=img)

        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        self.root.after(30, self.update_frame)


# run it!!
if __name__ == "__main__":
    init_db()

    rtsp_url = "rtsp://192.168.20.100:554/live.sdp"

    model = YOLOModel()
    video_stream = VideoStream(rtsp_url)

    root = tk.Tk()
    app = TrafficMonitorApp(root, model, video_stream)
    root.mainloop()

    video_stream.release()
