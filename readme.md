# FPS Limiter (Proof of Concept)

This project is a non-functional proof of concept for a tool that can limit the FPS of other running applications on Windows.

The core idea is to build a Python GUI that allows a user to select a running application, set a desired FPS limit, and apply it on the fly. This is achieved by injecting a custom C++ DLL into the target application.

**This is a proof of concept and the code is not functional out-of-the-box. It requires a C++ compiler and developer expertise to complete.**

## How It Works

The project is split into two main parts: a Python-based user interface and a C++-based DLL for injection.

1.  **Python GUI (`main_ui.py`)**:
    *   Uses `tkinter` for the user interface.
    *   Uses `app_lister.py` to get a list of all running applications that have a visible window.
    *   Displays the applications in a list for the user to select.
    *   Provides an input box to set the desired FPS limit.

2.  **Inter-Process Communication (IPC)**:
    *   When the user clicks "Set FPS Limit", the Python app writes the desired FPS number into a file named `fps_limit.txt`.

3.  **DLL Injection (`injector.py`)**:
    *   The Python app then uses `injector.py` to inject the `fps_limiter.dll` into the target application's process.
    *   The injection is done by using the Windows API via Python's `ctypes` library.

4.  **The C++ DLL (`fps_limiter_dll.cpp`)**:
    *   Once injected into the target application, the DLL hooks the application's rendering function (e.g., DirectX's `Present` function). This requires a hooking library like MinHook or Microsoft Detours.
    *   The hook periodically reads the `fps_limit.txt` file to check for any changes to the FPS limit.
    *   It then introduces a `sleep` delay between frames to ensure the application does not exceed the specified FPS.

## Project Structure

-   `main_ui.py`: The main entry point for the application. Run this file to launch the GUI.
-   `app_lister.py`: A module that uses `pywin32` and `psutil` to find and list running applications.
-   `injector.py`: A module that contains the logic for injecting a DLL into another process.
-   `fps_limiter_dll.cpp`: The C++ source code for the DLL. **This needs to be compiled.**
-   `requirements.txt`: A list of the required Python packages.
-   `readme.md`: This file.

## How to Build and Run (Hypothetical)

This is a guide for how a developer would take this proof of concept and make it functional.

### 1. Prerequisites
-   Python 3
-   A C++ compiler (e.g., Visual Studio with the C++ toolchain)
-   A C++ hooking library (e.g., [MinHook](https://github.com/TsudaKageyu/minhook))

### 2. Install Python Dependencies
Install the required Python packages from the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 3. Compile the C++ DLL
1.  Set up a new C++ DLL project in Visual Studio.
2.  Add `fps_limiter_dll.cpp` to the project.
3.  Add the MinHook library to your project (or your hooking library of choice).
4.  Modify the `DllMain` function in `fps_limiter_dll.cpp` to include the actual hooking logic (the current code contains pseudocode for this). You will need to find the address of the target rendering function.
5.  Compile the project to produce `fps_limiter.dll`.
6.  Place the compiled `fps_limiter.dll` in the same directory as the Python scripts.

### 4. Run the Application
Once the DLL is compiled and in the correct location, you can run the main Python application:
```bash
python main_ui.py
```

1.  The GUI should appear.
2.  Click "Refresh List" to see the list of running applications.
3.  Select an application from the list.
4.  Enter your desired FPS limit in the box.
5.  Click "Set FPS Limit".

If everything is set up correctly, the DLL will be injected and the target application's frame rate should be limited.
