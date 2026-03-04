import asyncio
import cv2
import time
from universal_vision_mcp.camera import MockCamera

def main():
    print("Launching Mock Camera preview with HUD...")
    cam = MockCamera(name="mock_cam")
    # Enable live preview window
    cam.set_preview(True)
    cam.start()
    
    print("\n--- INSTRUCTIONS ---")
    print("1. A window 'Universal Vision: mock_cam' should appear.")
    print("2. Take your screenshot of the HUD (arrows, crosshair, etc.).")
    print("3. Press 'q' in the window or Ctrl+C here to exit.")
    print("---------------------\n")
    
    try:
        while True:
            time.sleep(1)
            # Check if user disabled preview via 'q' key in the camera loop
            if not cam.preview_enabled:
                break
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        cam.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
