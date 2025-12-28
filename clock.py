import time
import pygame
import tkinter as tk
from tkinter import ttk, font
from datetime import datetime, timedelta
from typing import Tuple

# ============================================================
# CONFIG / DEFAULTS
# ============================================================

TERMINA_HOURS_PER_DAY = 24
TERMINA_TOTAL_HOURS = 72  # 3 Termina days

# Audio files
AUDIO_HOUR = "hour.mp3"
AUDIO_FINAL = "final.mp3"
AUDIO_BELLS = "bells.mp3"

# Real-time cycle lengths
REAL_SECONDS_72MIN = 72 * 60          # 72-minute Majora's Mask style
REAL_SECONDS_24HR = 24 * 60 * 60      # 24-hour real-day cycle

# Global settings (can be changed via Settings menu)
cycle_mode = "72min"  # "72min" or "24hr"
mute_hour = False
mute_final = False    # Affects both final.mp3 and bells.mp3

# Debug settings
debug_mode = False
debug_time_offset = 0.0  # Manual time offset in seconds
show_seconds = False  # Toggle to show seconds in clock display

# Theme settings
dark_mode = False

# Theme colors
THEME = {
    "light": {
        "bg": "#FFFFFF",
        "fg": "#000000",
        "label_bg": "#FFFFFF",
        "label_fg": "#000000"
    },
    "dark": {
        "bg": "#1E1E1E",
        "fg": "#FFFFFF",
        "label_bg": "#2D2D2D",
        "label_fg": "#FFFFFF"
    }
}

# Epoch: real-world timestamp when the cycle ends
epoch_end_timestamp = time.time() + REAL_SECONDS_72MIN  # default: 72 mins from launch

# ============================================================
# AUDIO SETUP
# ============================================================

pygame.mixer.init()

def play_sound(file, muted=False):
    """Play a given mp3 file if not muted.
    
    Args:
        file (str): Path to audio file
        muted (bool): Whether sound is muted
    """
    if muted:
        return
    try:
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing {file}: {e}")

def stop_sound():
    """Stop any currently playing music."""
    try:
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"Error stopping sound: {e}")

# ============================================================
# TERMINA TIME ENGINE
# ============================================================

def set_epoch_end(real_timestamp):
    """Set the real-world timestamp when the 72-hour Termina cycle ends.
    
    Args:
        real_timestamp (float): Unix timestamp
    """
    global epoch_end_timestamp
    epoch_end_timestamp = real_timestamp

def get_cycle_length_seconds():
    """Return the real-world seconds for the current cycle mode.
    
    Returns:
        int: Seconds in cycle
    """
    if cycle_mode == "72min":
        return REAL_SECONDS_72MIN
    else:
        return REAL_SECONDS_24HR

def advance_debug_time(seconds: float):
    """Advance the debug time offset for manual time progression.
    
    Args:
        seconds (float): Number of seconds to advance (can be negative)
    """
    global debug_time_offset
    debug_time_offset += seconds
    direction = "forward" if seconds > 0 else "backward"
    print(f"Debug time moved {direction} by {abs(seconds)}s. New offset: {debug_time_offset}s")

def reset_debug_time():
    """Reset the debug time offset to zero."""
    global debug_time_offset
    debug_time_offset = 0.0
    print("Debug time offset reset to 0s")

def set_debug_time_offset(seconds: float):
    """Set the debug time offset to a specific value.
    
    Args:
        seconds (float): Time offset in seconds
    """
    global debug_time_offset
    debug_time_offset = seconds
    print(f"Debug time offset set to {seconds}s")

def apply_theme():
    """Apply the current theme to all UI elements."""
    global dark_mode
    theme = THEME["dark"] if dark_mode else THEME["light"]
    
    root.configure(bg=theme["bg"])
    label.configure(bg=theme["label_bg"], fg=theme["label_fg"])
    
    # Update menu colors if menu exists
    if 'menu' in globals():
        menu.configure(bg=theme["bg"], fg=theme["fg"])

def get_termina_state():
    """
    Calculate Termina state based on epoch and cycle mode.

    Returns:
        Tuple containing:
        - day (int): 1-3
        - hour (float): 0-23.x
        - total_hours (float): 0-72.x Termina hours elapsed
        - seconds_remaining (float): real seconds until cycle reset (epoch)
    """
    now = time.time() + debug_time_offset
    seconds_remaining = epoch_end_timestamp - now

    # Clamp at 0 when past the epoch
    if seconds_remaining < 0:
        seconds_remaining = 0

    cycle_real_seconds = get_cycle_length_seconds()

    # Progress through the cycle: 0.0 (start) → 1.0 (end)
    if cycle_real_seconds <= 0:
        progress = 1.0
    else:
        progress = 1 - (seconds_remaining / cycle_real_seconds)
        if progress < 0:
            progress = 0
        if progress > 1:
            progress = 1

    # Map progress onto 0–72 Termina hours
    total_hours = progress * TERMINA_TOTAL_HOURS  # 0–72

    # Termina day and hour
    day = int(total_hours // TERMINA_HOURS_PER_DAY) + 1
    if day > 3:
        day = 3  # clamp for safety

    hour = total_hours % TERMINA_HOURS_PER_DAY  # 0–23.x

    return day, hour, total_hours, seconds_remaining

# ============================================================
# UI SETUP
# ============================================================

root = tk.Tk()
root.title("Termina Clock")
root.geometry("500x280")

# Try to load custom font, fallback to Consolas if not available
try:
    import os
    font_path = os.path.abspath("font.ttf")
    if os.path.exists(font_path):
        # Try multiple approaches to load the custom font
        try:
            # Method 1: Try using the font file path directly
            label = tk.Label(root, text="", font=(font_path, 22), justify="center")
            print("Custom font loaded using file path")
        except tk.TclError:
            try:
                # Method 2: Try using font.Font with file
                custom_font = font.Font(family="CustomFont", size=22)
                label = tk.Label(root, text="", font=custom_font, justify="center")
                print("Custom font loaded using Font object")
            except tk.TclError:
                # Method 3: Try just the filename
                label = tk.Label(root, text="", font=("font.ttf", 22), justify="center")
                print("Custom font loaded using filename")
    else:
        raise FileNotFoundError("Font file not found")
except Exception as e:
    print(f"Custom font not available ({e}), using Consolas fallback")
    label = tk.Label(root, text="", font=("Consolas", 22), justify="center")

label.pack(expand=True)

# Apply initial theme
apply_theme()

# ============================================================
# SETTINGS WINDOW
# ============================================================

def open_settings():
    """Open the settings window with debug controls."""
    global cycle_mode, mute_hour, mute_final, debug_mode, show_seconds, dark_mode

    settings = tk.Toplevel(root)
    settings.title("Settings")
    settings.geometry("450x600")

    # --- Epoch time entry ---
    tk.Label(settings, text="Day 3 ends at (HH:MM 24h, today or tomorrow):").pack(pady=(10, 0))
    epoch_entry = tk.Entry(settings)
    epoch_entry.pack()

    # Show a hint of current epoch time
    current_epoch = datetime.fromtimestamp(epoch_end_timestamp)
    epoch_entry.insert(0, current_epoch.strftime("%H:%M"))

    # --- Cycle length toggle ---
    tk.Label(settings, text="Cycle length:").pack(pady=(10, 0))
    cycle_var = tk.StringVar(value=cycle_mode)

    ttk.Radiobutton(
        settings, text="72-minute cycle (classic)",
        variable=cycle_var, value="72min"
    ).pack(anchor="w", padx=20)

    ttk.Radiobutton(
        settings, text="24-hour real-day cycle",
        variable=cycle_var, value="24hr"
    ).pack(anchor="w", padx=20)

    # --- Mute toggles ---
    hour_var = tk.BooleanVar(value=mute_hour)
    final_var = tk.BooleanVar(value=mute_final)

    tk.Checkbutton(settings, text="Mute hour.mp3 (day/night chime)",
                   variable=hour_var).pack(pady=(10, 0), anchor="w", padx=20)

    tk.Checkbutton(settings, text="Mute final.mp3 and bells.mp3 (final night)",
                   variable=final_var).pack(anchor="w", padx=20)

    # --- Display Options ---
    tk.Label(settings, text="Display Options:", font=("Arial", 10, "bold")).pack(pady=(15, 5))
    
    seconds_var = tk.BooleanVar(value=show_seconds)
    tk.Checkbutton(settings, text="Show seconds in clock display",
                   variable=seconds_var).pack(anchor="w", padx=20)
    
    dark_var = tk.BooleanVar(value=dark_mode)
    tk.Checkbutton(settings, text="Dark mode",
                   variable=dark_var).pack(anchor="w", padx=20)

    # --- Debug Section ---
    tk.Label(settings, text="Debug Controls:", font=("Arial", 10, "bold")).pack(pady=(15, 5))
    
    debug_var = tk.BooleanVar(value=debug_mode)
    tk.Checkbutton(settings, text="Enable Debug Mode",
                   variable=debug_var).pack(anchor="w", padx=20)
    
    tk.Label(settings, text="Time Offset (seconds, negative = past):").pack(pady=(5, 0))
    debug_offset_entry = tk.Entry(settings)
    debug_offset_entry.pack()
    debug_offset_entry.insert(0, str(debug_time_offset))
    
    # Forward time controls
    tk.Label(settings, text="Time Controls:", font=("Arial", 9)).pack(pady=(10, 5))
    forward_frame = tk.Frame(settings)
    forward_frame.pack()
    
    tk.Button(forward_frame, text="+1 Hour", 
              command=lambda: advance_debug_time(3600)).pack(side="left", padx=2)
    tk.Button(forward_frame, text="+10 Min", 
              command=lambda: advance_debug_time(600)).pack(side="left", padx=2)
    tk.Button(forward_frame, text="+1 Min", 
              command=lambda: advance_debug_time(60)).pack(side="left", padx=2)
    
    # Backward time controls
    backward_frame = tk.Frame(settings)
    backward_frame.pack()
    
    tk.Button(backward_frame, text="-1 Hour", 
              command=lambda: advance_debug_time(-3600)).pack(side="left", padx=2)
    tk.Button(backward_frame, text="-10 Min", 
              command=lambda: advance_debug_time(-600)).pack(side="left", padx=2)
    tk.Button(backward_frame, text="-1 Min", 
              command=lambda: advance_debug_time(-60)).pack(side="left", padx=2)
    tk.Button(backward_frame, text="Reset", 
              command=reset_debug_time).pack(side="left", padx=2)

    def save_settings():
        """Save settings from the settings window."""
        global cycle_mode, mute_hour, mute_final, debug_mode, show_seconds, dark_mode

        # Mute options
        mute_hour = hour_var.get()
        mute_final = final_var.get()
        debug_mode = debug_var.get()
        show_seconds = seconds_var.get()
        dark_mode = dark_var.get()
        
        # Apply theme after setting dark_mode
        apply_theme()

        # Cycle mode
        cycle_mode = cycle_var.get()

        # Parse epoch time (HH:MM) - this is when Day 3 should end
        t = epoch_entry.get().strip()
        if t:
            try:
                if ":" in t:
                    hh, mm = map(int, t.split(":"))
                else:
                    # Handle just hours (e.g., "14")
                    hh = int(t)
                    mm = 0
                
                if not (0 <= hh <= 23 and 0 <= mm <= 59):
                    raise ValueError("Invalid time range")
                    
                now = datetime.now()
                # Calculate when Day 3 should end at the specified time
                target_day3_end = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                
                # If target time already passed today, assume tomorrow
                if target_day3_end.timestamp() <= time.time():
                    target_day3_end = target_day3_end + timedelta(days=1)
                
                # Calculate the start time (when Day 1 begins)
                # Day 3 ends at target_time, so we need to subtract 2 full days of Termina time
                cycle_length = get_cycle_length_seconds()
                day1_start = target_day3_end.timestamp() - cycle_length
                
                set_epoch_end(target_day3_end.timestamp())
                print(f"Day 3 will end at: {target_day3_end.strftime('%Y-%m-%d %H:%M')}")
                print(f"Day 1 started at: {datetime.fromtimestamp(day1_start).strftime('%Y-%m-%d %H:%M')}")
            except ValueError as e:
                print(f"Invalid time format '{t}'. Use HH:MM format. Error: {e}")
            except Exception as e:
                print(f"Error parsing epoch time '{t}': {e}")

        # Parse debug time offset
        debug_offset_str = debug_offset_entry.get().strip()
        if debug_offset_str:
            try:
                offset = float(debug_offset_str)
                set_debug_time_offset(offset)
                print(f"Debug time offset set to: {offset} seconds")
            except ValueError:
                print(f"Invalid debug offset '{debug_offset_str}'. Use number in seconds.")

        settings.destroy()

    tk.Button(settings, text="Save", command=save_settings).pack(pady=15)

# Menu bar (create after function definition)
menu = tk.Menu(root)
menu.add_command(label="Settings", command=open_settings)
root.config(menu=menu)

# ============================================================
# MAIN LOOP / EVENT LOGIC
# ============================================================

last_hour_int = -1
final_music_playing = False
bells_playing = False

def update_clock():
    """Main clock update function with debug support."""
    global last_hour_int, final_music_playing, bells_playing

    day, hour, total_hours, seconds_remaining = get_termina_state()
    hour_int = int(hour)

    # Show debug info if debug mode is enabled
    if debug_mode:
        debug_info = f"\n[DEBUG] Offset: {debug_time_offset:.1f}s"
        if seconds_remaining > 0:
            debug_info += f"\n[DEBUG] Real remaining: {seconds_remaining:.1f}s"
    else:
        debug_info = ""

    # -------------------------------
    # FINAL NIGHT MUSIC (final.mp3)
    # Day 3, 18:00 and onwards, but not in last 5 minutes
    # -------------------------------
    if seconds_remaining > 300:  # more than 5 minutes remaining
        if day == 3 and hour >= 18 and not final_music_playing:
            stop_sound()
            play_sound(AUDIO_FINAL, muted=mute_final)
            final_music_playing = True
            bells_playing = False
    else:
        # We're in the final 5 minutes, final.mp3 should not be playing
        final_music_playing = False

    # -------------------------------
    # FINAL COUNTDOWN (last 5 real minutes)
    # Switch to bells.mp3 and show ms countdown
    # -------------------------------
    if 0 < seconds_remaining <= 300:
        if not bells_playing:
            stop_sound()
            play_sound(AUDIO_BELLS, muted=mute_final)
            bells_playing = True

        # Real-time countdown with milliseconds
        whole_sec = int(seconds_remaining)
        ms = int((seconds_remaining - whole_sec) * 1000)
        label.config(
            text=f"FINAL HOURS\n{whole_sec:02d}.{ms:03d} seconds remain{debug_info}"
        )

    else:
        bells_playing = False

        # -------------------------------
        # DAY/NIGHT TRANSITIONS (06:00 and 18:00)
        # Play hour.mp3 when crossing those hours
        # -------------------------------
        if hour_int != last_hour_int:
            if hour_int in (6, 18):
                play_sound(AUDIO_HOUR, muted=mute_hour)
        last_hour_int = hour_int

        # Normal display (no final countdown)
        if show_seconds:
            # Calculate actual seconds within the Termina hour (0-59)
            hour_fraction = hour % 1
            display_seconds = int(hour_fraction * 60)  # Convert fractional hour to 0-59 seconds
            
            label.config(
                text=f"Day {day}\n{hour_int:02d}:{display_seconds:02d} Termina{debug_info}"
            )
        else:
            label.config(
                text=f"Day {day}\n{hour_int:02d}:00 Termina{debug_info}"
            )

    # -------------------------------
    # RESET EVENT (cycle ended)
    # -------------------------------
    if seconds_remaining <= 0:
        # Cycle has ended. Just show reset text.
        label.config(text=f"DAWN OF A NEW DAY{debug_info}")
        stop_sound()
        final_music_playing = False
        bells_playing = False
        # You could auto-advance to next cycle here if you want.

    # Update ~20 times per second for a smooth ms countdown
    root.after(50, update_clock)

update_clock()
root.mainloop()
