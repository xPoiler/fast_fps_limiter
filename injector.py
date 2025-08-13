"""
    DLL Injector - Proof of Concept

    This is a NON-FUNCTIONAL proof of concept. It is intended to be used with
    the compiled `fps_limiter.dll` from `fps_limiter_dll.cpp`.

    This script requires the `psutil` library to find the process ID (`pip install psutil`).

    The steps for DLL injection are:
    1.  Find the Process ID (PID) of the target application (e.g., "game.exe").
    2.  Get a "handle" to the process, which gives us the necessary permissions to interact with it.
    3.  Allocate some memory within the target process's address space.
    4.  Write the full path to our DLL (`C:\\path\\to\\fps_limiter.dll`) into that allocated memory.
    5.  Find the memory address of the `LoadLibraryA` function from `kernel32.dll`. This function
        is a standard Windows function that can load a DLL into a process.
    6.  Create a new thread inside the target process that starts by running `LoadLibraryA`, with the
        address of our DLL path as its argument. This forces the target process to load our DLL.
"""

import ctypes
from ctypes import wintypes
import psutil
import os

# Define necessary Windows structures and function prototypes using ctypes
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Process access rights
PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)

# Memory allocation types
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000

# Memory protection constants
PAGE_READWRITE = 0x04

# Function prototypes
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.VirtualAllocEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
kernel32.VirtualAllocEx.restype = wintypes.LPVOID

kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.WriteProcessMemory.restype = wintypes.BOOL

kernel32.GetProcAddress.argtypes = [wintypes.HMODULE, wintypes.LPCSTR]
kernel32.GetProcAddress.restype = wintypes.LPVOID

kernel32.CreateRemoteThread.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID]
kernel32.CreateRemoteThread.restype = wintypes.HANDLE

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

def find_pid_by_name(process_name):
    """Finds the Process ID (PID) for a given process name."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc.info['pid']
    return None

def inject_dll(pid, dll_path):
    """Injects a DLL into the process with the given PID."""
    if not os.path.exists(dll_path):
        print(f"Error: DLL not found at '{dll_path}'")
        return False

    print(f"Attempting to inject '{dll_path}' into PID: {pid}")

    # 1. Get a handle to the process
    proc_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not proc_handle:
        print(f"Error: Could not open process with PID {pid}. Error code: {ctypes.get_last_error()}")
        return False

    # 2. Allocate memory for the DLL path in the target process
    dll_path_bytes = dll_path.encode('ascii')
    mem_addr = kernel32.VirtualAllocEx(proc_handle, None, len(dll_path_bytes) + 1, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
    if not mem_addr:
        print(f"Error: Could not allocate memory in target process. Error code: {ctypes.get_last_error()}")
        kernel32.CloseHandle(proc_handle)
        return False

    # 3. Write the DLL path to the allocated memory
    bytes_written = ctypes.c_size_t(0)
    if not kernel32.WriteProcessMemory(proc_handle, mem_addr, dll_path_bytes, len(dll_path_bytes) + 1, ctypes.byref(bytes_written)):
        print(f"Error: Could not write to process memory. Error code: {ctypes.get_last_error()}")
        # Clean up and return
        kernel32.VirtualFreeEx(proc_handle, mem_addr, 0, MEM_RELEASE)
        kernel32.CloseHandle(proc_handle)
        return False

    print("Memory allocated and DLL path written successfully.")

    # 4. Get the address of the LoadLibraryA function
    load_library_addr = kernel32.GetProcAddress(kernel32.GetModuleHandleW('kernel32.dll'), b'LoadLibraryA')
    if not load_library_addr:
        print(f"Error: Could not find LoadLibraryA address. Error code: {ctypes.get_last_error()}")
        # Clean up and return
        kernel32.VirtualFreeEx(proc_handle, mem_addr, 0, MEM_RELEASE)
        kernel32.CloseHandle(proc_handle)
        return False

    # 5. Create a remote thread in the target process to load the DLL
    thread_handle = kernel32.CreateRemoteThread(proc_handle, None, 0, load_library_addr, mem_addr, 0, None)
    if not thread_handle:
        print(f"Error: Could not create remote thread. Error code: {ctypes.get_last_error()}")
        # Clean up and return
        kernel32.VirtualFreeEx(proc_handle, mem_addr, 0, MEM_RELEASE)
        kernel32.CloseHandle(proc_handle)
        return False

    print("Successfully created remote thread. DLL should now be injected.")

    # 6. Clean up
    # Note: We don't free the allocated memory for the DLL path because the DLL needs it.
    # A more robust solution would have the DLL free its own path memory once it's loaded.
    kernel32.CloseHandle(thread_handle)
    kernel32.CloseHandle(proc_handle)
    return True


if __name__ == "__main__":
    # --- USAGE EXAMPLE ---
    # This is how you would use the injector.
    # You would need to replace "notepad.exe" with the target game's executable.
    # The DLL path must be an absolute path.

    target_process_name = "notepad.exe" # Example target

    # IMPORTANT: This DLL path must be absolute and the DLL must be compiled from the C++ source.
    # Since we cannot compile it, this script will fail unless you provide a valid DLL.
    dll_name = "fps_limiter.dll"
    dll_full_path = os.path.abspath(dll_name)

    pid = find_pid_by_name(target_process_name)

    if pid:
        print(f"Found '{target_process_name}' with PID {pid}.")
        inject_dll(pid, dll_full_path)
    else:
        print(f"Process '{target_process_name}' not found. Is it running?")
