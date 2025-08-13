import tkinter as tk
from tkinter import messagebox
import os
import app_lister
import injector

class FpsLimiterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FPS Limiter (Proof of Concept)")

        self.apps = []

        # --- UI Elements ---
        self.main_frame = tk.Frame(root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Listbox with Scrollbar
        list_frame = tk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.app_list_label = tk.Label(list_frame, text="Select Application to Limit:")
        self.app_list_label.pack(anchor=tk.W)

        self.app_list_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.app_list = tk.Listbox(list_frame, yscrollcommand=self.app_list_scrollbar.set, width=70)
        self.app_list_scrollbar.config(command=self.app_list.yview)

        self.app_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.app_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_button = tk.Button(self.main_frame, text="Refresh List", command=self.refresh_app_list)
        self.refresh_button.pack(pady=5)

        # Controls Frame
        controls_frame = tk.Frame(self.main_frame)
        controls_frame.pack(fill=tk.X, pady=10)

        self.fps_label = tk.Label(controls_frame, text="FPS Limit:")
        self.fps_label.pack(side=tk.LEFT, padx=(0, 5))

        self.fps_entry = tk.Entry(controls_frame, width=10)
        self.fps_entry.pack(side=tk.LEFT)
        self.fps_entry.insert(0, "60")

        self.set_button = tk.Button(controls_frame, text="Set FPS Limit", command=self.set_fps_limit)
        self.set_button.pack(side=tk.RIGHT)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Refresh the list to see running applications.")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padx=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Initial population of the list
        self.refresh_app_list()

    def refresh_app_list(self):
        """Fetches the list of running applications and updates the listbox."""
        self.status_var.set("Refreshing application list...")
        self.root.update_idletasks()

        self.apps = app_lister.get_running_applications()
        self.app_list.delete(0, tk.END)

        for app in sorted(self.apps, key=lambda x: x['name']):
            display_text = f"{app['name']:<25} | PID: {app['pid']:<6} | {app['title']}"
            self.app_list.insert(tk.END, display_text)

        self.status_var.set(f"Found {len(self.apps)} applications. Ready.")

    def set_fps_limit(self):
        """The main function to set the FPS limit on the selected application."""
        selected_indices = self.app_list.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select an application from the list.")
            return

        # Find the selected application's data
        selected_index = selected_indices[0]
        selected_app_display = self.app_list.get(selected_index)
        pid_str = selected_app_display.split("PID:")[1].strip().split(" ")[0]
        selected_pid = int(pid_str)

        # Get desired FPS from entry
        try:
            fps_limit = int(self.fps_entry.get())
            if fps_limit <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid, positive number for the FPS limit.")
            return

        # 1. Write the FPS limit to the IPC file
        try:
            with open("fps_limit.txt", "w") as f:
                f.write(str(fps_limit))
            self.status_var.set(f"Wrote FPS limit '{fps_limit}' to ipc file.")
            self.root.update_idletasks()
        except IOError as e:
            messagebox.showerror("Error", f"Could not write to fps_limit.txt: {e}")
            self.status_var.set("Error writing to IPC file.")
            return

        # 2. Inject the DLL
        # NOTE: This part is a proof of concept and requires the C++ code to be compiled into a DLL.
        dll_name = "fps_limiter.dll"
        dll_full_path = os.path.abspath(dll_name)

        if not os.path.exists(dll_full_path):
            messagebox.showwarning(
                "Proof of Concept",
                f"The injector is about to run, but the required '{dll_name}' was not found.\n\n"
                f"This is expected since the C++ code has not been compiled.\n\n"
                f"The application will now proceed with the injection attempt for demonstration purposes."
            )

        self.status_var.set(f"Attempting to inject DLL into PID {selected_pid}...")
        self.root.update_idletasks()

        if injector.inject_dll(selected_pid, dll_full_path):
            messagebox.showinfo("Success", f"Successfully initiated injection process for PID {selected_pid}.\n\nThe FPS limit of {fps_limit} should now be active.")
            self.status_var.set(f"Injection successful for PID {selected_pid}.")
        else:
            messagebox.showerror("Injection Failed", f"Failed to inject DLL into PID {selected_pid}.\n\nMake sure the application is running with the correct permissions.")
            self.status_var.set(f"Injection failed for PID {selected_pid}.")


if __name__ == "__main__":
    root = tk.Tk()
    app = FpsLimiterApp(root)
    root.mainloop()
