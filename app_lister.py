import win32gui
import win32process
import psutil

def enum_windows_proc(hwnd, lParam):
    """Callback function for EnumWindows."""
    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
        # Get the process ID (PID) for the window
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        try:
            # Get the process name from the PID
            process = psutil.Process(pid)
            process_name = process.name()

            # We only want to list unique PIDs, as a single process can have multiple windows
            # The lParam is a dictionary where keys are PIDs
            if pid not in lParam:
                lParam[pid] = {
                    'hwnd': hwnd,
                    'title': win32gui.GetWindowText(hwnd),
                    'pid': pid,
                    'name': process_name
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Handle cases where the process might have died or is inaccessible
            pass
    return True

def get_running_applications():
    """
    Returns a list of dictionaries, where each dictionary contains information
    about a running application with a visible window.
    """
    # Use a dictionary to store unique processes by PID, then convert to a list
    apps_by_pid = {}
    win32gui.EnumWindows(enum_windows_proc, apps_by_pid)
    return list(apps_by_pid.values())

if __name__ == "__main__":
    applications = get_running_applications()
    print("Running Applications:")
    # Sort by process name for cleaner output
    for app in sorted(applications, key=lambda x: x['name']):
        print(f"- PID: {app['pid']:<6} | Name: {app['name']:<25} | Title: {app['title']}")
