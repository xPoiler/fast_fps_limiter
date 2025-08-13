/*
    FPS Limiter DLL - Proof of Concept (v2)

    This version is updated to use a simple file-based IPC.
    The Python GUI will write the desired FPS to "fps_limit.txt",
    and this DLL will read it.
*/

#include <windows.h>
#include <chrono>
#include <thread>
#include <fstream>
#include <string>

// Forward declaration for conceptual code
struct IDXGISwapChain;

// --- IPC Configuration ---
const char* IPC_FILE_PATH = "fps_limit.txt";
int g_fps_limit = 60; // Default FPS limit

// --- Hooking Setup ---
typedef HRESULT(WINAPI* Present_t)(IDXGISwapChain* pSwapChain, UINT SyncInterval, UINT Flags);
Present_t g_original_present = nullptr;

// --- Frame Timing & IPC ---
long long g_last_frame_time_ns = 0;
long long g_last_ipc_check_time_ns = 0;

// Function to read the FPS limit from the file
void UpdateFpsLimitFromFile() {
    std::ifstream ipc_file(IPC_FILE_PATH);
    if (ipc_file.is_open()) {
        std::string line;
        if (std::getline(ipc_file, line)) {
            try {
                int new_limit = std::stoi(line);
                if (new_limit > 0) {
                    g_fps_limit = new_limit;
                }
            } catch (...) {
                // Ignore conversion errors
            }
        }
        ipc_file.close();
    }
}


// --- The Hooked Function ---
HRESULT WINAPI HookedPresent(IDXGISwapChain* pSwapChain, UINT SyncInterval, UINT Flags)
{
    long long current_time_ns = std::chrono::high_resolution_clock::now().time_since_epoch().count();

    // Periodically check the IPC file for updates (e.g., every second)
    if (current_time_ns - g_last_ipc_check_time_ns > 1000000000) {
        UpdateFpsLimitFromFile();
        g_last_ipc_check_time_ns = current_time_ns;
    }

    if (g_last_frame_time_ns != 0 && g_fps_limit > 0) {
        long long target_frame_duration_ns = 1000000000 / g_fps_limit;
        long long time_spent_ns = current_time_ns - g_last_frame_time_ns;

        if (time_spent_ns < target_frame_duration_ns) {
            std::this_thread::sleep_for(std::chrono::nanoseconds(target_frame_duration_ns - time_spent_ns));
        }
    }

    g_last_frame_time_ns = std::chrono::high_resolution_clock::now().time_since_epoch().count();

    return g_original_present(pSwapChain, SyncInterval, Flags);
}

// --- DLL Entry Point ---
BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved)
{
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(hModule);
        // On attach, do an initial read of the IPC file.
        UpdateFpsLimitFromFile();
        // PSEUDOCODE: Hooking logic would go here.
        break;

    case DLL_PROCESS_DETACH:
        // PSEUDOCODE: Unhooking logic would go here.
        break;
    }
    return TRUE;
}
