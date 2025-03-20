import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, font
import pyautogui
import time
import threading
import queue
import random
import json
import os
import sys
import math
import re
from datetime import datetime
import keyboard
import platform

# Optional imports with fallbacks
try:
    import pystray
    from PIL import Image, ImageDraw, ImageTk, ImageFilter, ImageEnhance
    HAS_SYSTEM_TRAY = True
    HAS_PIL = True
except ImportError:
    HAS_SYSTEM_TRAY = False
    HAS_PIL = False

try:
    import pygame
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class EnhancedStealthTyper:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Stealth Auto-Typer")
        self.root.geometry("850x680")
        
        # Create version and initialize
        self.version = "2.0"
        
        # State variables
        self.is_typing = False
        self.is_paused = False
        self.typing_thread = None
        self.queue = queue.Queue()
        self.system_tray_icon = None
        self.last_window_state = {}
        self.mini_panel = None
        
        # Current typing stats
        self.chars_typed = 0
        self.total_chars = 0
        self.start_time = 0
        self.current_char_preview = ""
        self.preview_index = 0
        self.typing_animation_chars = 0  # For animating the preview
        
        # Sound effects
        self.sound_initialized = False
        self.sound_enabled = False
        
        # Initialize theme settings
        self.theme_mode = "dark"  # Default to dark theme for stealthiness
        
        # Typing profiles - enhanced with more realistic patterns
        self.typing_profiles = {
            "Executive": {
                "base_wpm": 75,
                "wpm_variation": 15,
                "error_rate": 1.5,
                "smart_pauses": True,
                "pause_multiplier": {
                    ".": 3.0,
                    ",": 1.8,
                    ";": 2.0,
                    ":": 2.0,
                    "?": 3.2,
                    "!": 3.0,
                    "(": 1.2,
                    ")": 1.2,
                    "{": 1.5,
                    "}": 1.5,
                    "\n": 3.5,
                    "\t": 1.5
                },
                "word_burst": True,
                "burst_probability": 0.5,
                "burst_speed_multiplier": 1.5,
                "typing_rhythm": "natural",
                "key_press_duration": (0.01, 0.04),
                "sound_profile": "mechanical",
                "description": "Professional, precise typing with minimal errors"
            },
            "Programmer": {
                "base_wpm": 85,
                "wpm_variation": 20,
                "error_rate": 1.2,
                "smart_pauses": True,
                "pause_multiplier": {
                    ".": 2.0,
                    ",": 1.5,
                    ";": 2.2,
                    ":": 1.5,
                    "?": 2.0,
                    "!": 2.0,
                    "(": 1.0,
                    ")": 1.0,
                    "{": 1.8,
                    "}": 1.8,
                    "\n": 2.5,
                    "\t": 1.2
                },
                "word_burst": True,
                "burst_probability": 0.6,
                "burst_speed_multiplier": 1.7,
                "typing_rhythm": "consistent",
                "key_press_duration": (0.01, 0.03),
                "sound_profile": "mechanical",
                "description": "Fast with occasional bursts, optimized for code"
            },
            "Natural": {
                "base_wpm": 55,
                "wpm_variation": 25,
                "error_rate": 3,
                "smart_pauses": True,
                "pause_multiplier": {
                    ".": 3.5,
                    ",": 2.0,
                    ";": 2.2,
                    ":": 2.2,
                    "?": 3.5,
                    "!": 3.5,
                    "(": 1.5,
                    ")": 1.5,
                    "{": 2.0,
                    "}": 2.0,
                    "\n": 4.0,
                    "\t": 2.0
                },
                "word_burst": True,
                "burst_probability": 0.4,
                "burst_speed_multiplier": 1.4,
                "typing_rhythm": "natural",
                "key_press_duration": (0.02, 0.06),
                "sound_profile": "standard",
                "description": "Average human typing patterns with natural variations"
            },
            "Realistic Student": {
                "base_wpm": 45,
                "wpm_variation": 30,
                "error_rate": 4,
                "smart_pauses": True,
                "pause_multiplier": {
                    ".": 4.0,
                    ",": 2.5,
                    ";": 2.5,
                    ":": 2.5,
                    "?": 4.0,
                    "!": 4.0,
                    "(": 2.0,
                    ")": 2.0,
                    "{": 2.5,
                    "}": 2.5,
                    "\n": 5.0,
                    "\t": 2.5
                },
                "word_burst": True,
                "burst_probability": 0.3,
                "burst_speed_multiplier": 1.3,
                "typing_rhythm": "irregular",
                "key_press_duration": (0.03, 0.08),
                "sound_profile": "soft",
                "description": "Less consistent typing with frequent pauses and errors"
            },
            "Ultra Stealth": {
                "base_wpm": 50,
                "wpm_variation": 35,
                "error_rate": 3.5,
                "smart_pauses": True,
                "pause_multiplier": {
                    ".": 4.2,
                    ",": 2.2,
                    ";": 2.3,
                    ":": 2.3,
                    "?": 4.2,
                    "!": 4.2,
                    "(": 1.6,
                    ")": 1.6,
                    "{": 2.2,
                    "}": 2.2,
                    "\n": 5.2,
                    "\t": 2.2
                },
                "word_burst": True,
                "burst_probability": 0.45,
                "burst_speed_multiplier": 1.5,
                "typing_rhythm": "ultra_natural",
                "key_press_duration": (0.02, 0.07),
                "thought_pause_probability": 0.08,
                "thought_pause_duration": (0.8, 3.0),
                "sound_profile": "quiet",
                "description": "Indistinguishable from human typing with random pauses"
            },
            "Custom": {
                "base_wpm": 60,
                "wpm_variation": 20,
                "error_rate": 2,
                "smart_pauses": True,
                "pause_multiplier": {
                    ".": 3.0,
                    ",": 2.0,
                    ";": 2.0,
                    ":": 2.0,
                    "?": 3.0,
                    "!": 3.0,
                    "(": 1.5,
                    ")": 1.5,
                    "{": 2.0,
                    "}": 2.0,
                    "\n": 4.0,
                    "\t": 2.0
                },
                "word_burst": True,
                "burst_probability": 0.4,
                "burst_speed_multiplier": 1.5,
                "typing_rhythm": "natural",
                "key_press_duration": (0.01, 0.05),
                "sound_profile": "standard",
                "description": "Fully customizable typing behavior"
            }
        }
        
        # Current typing profile
        self.current_profile = "Natural"
        self.active_profile = self.typing_profiles[self.current_profile].copy()
        
        # Settings dictionary
        self.settings = {
            "default_profile": "Natural",
            "hotkeys": {
                "start_typing": "ctrl+shift+f9",
                "pause_typing": "ctrl+shift+f10",
                "stop_typing": "ctrl+shift+f11",
                "show_app": "ctrl+shift+f12",
                "mini_panel": "ctrl+shift+space"
            },
            "startup_minimized": False,
            "always_on_top": False,
            "last_directory": os.path.expanduser("~"),
            "theme": "dark",
            "sound_enabled": True,
            "sound_volume": 0.3,
            "clipboard_monitoring": False,
            "mini_panel_enabled": True,
            "smooth_typing": True
        }
        
        # Load settings
        self.load_settings()
        
        # Initialize colors and styles
        self.init_colors()
        self.setup_styles()
        
        # Initialize sound effects if available
        if HAS_SOUND and self.settings["sound_enabled"]:
            self.init_sound()
        
        # Create the GUI
        self.create_gui()
        
        # Register global hotkeys
        self.register_hotkeys()
        
        # Start queue checker for thread communication
        self.check_queue()
        
        # Create the system tray icon if supported
        if HAS_SYSTEM_TRAY:
            self.setup_system_tray()
        
        # Create mini panel if enabled
        if self.settings["mini_panel_enabled"]:
            self.create_mini_panel()
        
        # Apply special platform-specific settings
        self.apply_platform_specifics()

    def init_colors(self):
        """Initialize color schemes for themes"""
        # Material Design inspired color schemes
        self.color_schemes = {
            "dark": {
                "bg_primary": "#121212",
                "bg_secondary": "#1e1e1e",
                "bg_tertiary": "#2d2d2d",
                "bg_input": "#373737",
                "fg_primary": "#ffffff",
                "fg_secondary": "#b3b3b3",
                "fg_tertiary": "#757575",
                "accent_primary": "#03dac6",  # Teal accent
                "accent_secondary": "#bb86fc", # Purple accent
                "accent_variant": "#018786",
                "success": "#4caf50",
                "warning": "#ffab40",
                "error": "#cf6679",
                "card_bg": "#1f1f1f",
                "card_hover": "#2a2a2a",
                "border": "#383838",
                "shadow": "#000000",
                "overlay": "#121212e0"
            },
            "light": {
                "bg_primary": "#f5f5f5",
                "bg_secondary": "#e0e0e0",
                "bg_tertiary": "#f0f0f0",
                "bg_input": "#ffffff",
                "fg_primary": "#202020",
                "fg_secondary": "#505050",
                "fg_tertiary": "#757575",
                "accent_primary": "#03dac6",
                "accent_secondary": "#6200ee",
                "accent_variant": "#018786",
                "success": "#4caf50",
                "warning": "#ff9800",
                "error": "#b00020",
                "card_bg": "#ffffff",
                "card_hover": "#f5f5f5",
                "border": "#e0e0e0",
                "shadow": "#bdbdbd",
                "overlay": "#f5f5f5e0"
            },
            "amoled": {  # Pure black theme for OLED displays
                "bg_primary": "#000000",
                "bg_secondary": "#0a0a0a",
                "bg_tertiary": "#151515",
                "bg_input": "#202020",
                "fg_primary": "#ffffff",
                "fg_secondary": "#b3b3b3",
                "fg_tertiary": "#757575",
                "accent_primary": "#00e5ff",
                "accent_secondary": "#a374ff",
                "accent_variant": "#00b7c7",
                "success": "#4caf50",
                "warning": "#ffab40",
                "error": "#ff5252",
                "card_bg": "#101010",
                "card_hover": "#1a1a1a",
                "border": "#2a2a2a",
                "shadow": "#000000",
                "overlay": "#000000e0"
            }
        }
        
        # Set current color scheme
        if self.theme_mode not in self.color_schemes:
            self.theme_mode = "dark"
        
        self.colors = self.color_schemes[self.theme_mode]

    def setup_styles(self):
        """Setup UI styles based on theme"""
        self.style = ttk.Style()
        
        # Try to use a modern theme if available
        available_themes = self.style.theme_names()
        preferred_themes = ['clam', 'alt', 'vista', 'xpnative', 'winnative']
        
        theme_to_use = 'clam'  # Default fallback
        for theme in preferred_themes:
            if theme in available_themes:
                theme_to_use = theme
                break
                
        self.style.theme_use(theme_to_use)
        
        # Configure custom styles
        self.style.configure('TFrame', background=self.colors["bg_primary"])
        self.style.configure('Secondary.TFrame', background=self.colors["bg_secondary"])
        self.style.configure('Card.TFrame', background=self.colors["card_bg"])
        
        self.style.configure('TLabel', 
                            background=self.colors["bg_primary"], 
                            foreground=self.colors["fg_primary"])
        self.style.configure('Secondary.TLabel', 
                            background=self.colors["bg_secondary"], 
                            foreground=self.colors["fg_secondary"])
        self.style.configure('Card.TLabel', 
                            background=self.colors["card_bg"], 
                            foreground=self.colors["fg_primary"])
        self.style.configure('Accent.TLabel', 
                            background=self.colors["bg_primary"], 
                            foreground=self.colors["accent_primary"])
        
        self.style.configure('TButton', 
                            background=self.colors["bg_secondary"], 
                            foreground=self.colors["fg_primary"])
        self.style.map('TButton', 
                      background=[('active', self.colors["bg_tertiary"])],
                      foreground=[('active', self.colors["fg_primary"])])
        
        self.style.configure('Accent.TButton', 
                            background=self.colors["accent_primary"], 
                            foreground=self.colors["bg_primary"])
        self.style.map('Accent.TButton', 
                      background=[('active', self.colors["accent_variant"])],
                      foreground=[('active', self.colors["bg_primary"])])
        
        self.style.configure('Success.TButton', 
                            background=self.colors["success"], 
                            foreground=self.colors["bg_primary"])
        self.style.map('Success.TButton', 
                      background=[('active', self.colors["success"])],
                      foreground=[('active', self.colors["bg_primary"])])
        
        self.style.configure('Warning.TButton', 
                            background=self.colors["warning"], 
                            foreground=self.colors["bg_primary"])
        self.style.map('Warning.TButton', 
                      background=[('active', self.colors["warning"])],
                      foreground=[('active', self.colors["bg_primary"])])
        
        self.style.configure('Error.TButton', 
                            background=self.colors["error"], 
                            foreground=self.colors["bg_primary"])
        self.style.map('Error.TButton', 
                      background=[('active', self.colors["error"])],
                      foreground=[('active', self.colors["bg_primary"])])
        
        self.style.configure('TCheckbutton', 
                            background=self.colors["bg_primary"], 
                            foreground=self.colors["fg_primary"])
        self.style.map('TCheckbutton', 
                      background=[('active', self.colors["bg_primary"])],
                      foreground=[('active', self.colors["fg_primary"])])
        
        self.style.configure('Card.TCheckbutton', 
                            background=self.colors["card_bg"], 
                            foreground=self.colors["fg_primary"])
        self.style.map('Card.TCheckbutton', 
                      background=[('active', self.colors["card_bg"])],
                      foreground=[('active', self.colors["fg_primary"])])
        
        self.style.configure('TRadiobutton', 
                            background=self.colors["bg_primary"], 
                            foreground=self.colors["fg_primary"])
        
        self.style.configure('TNotebook', 
                            background=self.colors["bg_primary"],
                            tabmargins=[2, 5, 2, 0])
        self.style.configure('TNotebook.Tab', 
                            background=self.colors["bg_secondary"], 
                            foreground=self.colors["fg_secondary"], 
                            padding=[15, 5])
        self.style.map('TNotebook.Tab', 
                      background=[('selected', self.colors["accent_primary"])],
                      foreground=[('selected', self.colors["bg_primary"])])
        
        self.style.configure('Horizontal.TProgressbar', 
                            background=self.colors["accent_primary"],
                            troughcolor=self.colors["bg_tertiary"])
        
        self.style.configure('Horizontal.TScale', 
                            background=self.colors["bg_primary"])
        self.style.map('Horizontal.TScale',
                      background=[('active', self.colors["bg_primary"])])
        
        self.style.configure('TCombobox', 
                            background=self.colors["bg_input"],
                            foreground=self.colors["fg_primary"],
                            fieldbackground=self.colors["bg_input"])
        self.style.map('TCombobox',
                      fieldbackground=[('readonly', self.colors["bg_input"])],
                      background=[('readonly', self.colors["bg_input"])],
                      foreground=[('readonly', self.colors["fg_primary"])])
        
        self.style.configure('TSpinbox', 
                            background=self.colors["bg_input"],
                            foreground=self.colors["fg_primary"],
                            fieldbackground=self.colors["bg_input"])
        
        # Update root config
        self.root.configure(bg=self.colors["bg_primary"])
        
        # Create custom fonts
        self.init_fonts()

    def init_fonts(self):
        """Initialize custom fonts"""
        # Get system-specific font choices
        if platform.system() == 'Windows':
            base_font = 'Segoe UI'
            mono_font = 'Consolas'
        elif platform.system() == 'Darwin':  # macOS
            base_font = 'SF Pro Text'
            mono_font = 'Menlo'
        else:  # Linux and others
            base_font = 'Ubuntu'
            mono_font = 'Ubuntu Mono'
            
        # Verify fonts are available, otherwise use fallbacks
        available_fonts = font.families()
        
        if base_font not in available_fonts:
            base_font = font.nametofont("TkDefaultFont").actual()["family"]
        
        if mono_font not in available_fonts:
            mono_font = font.nametofont("TkFixedFont").actual()["family"]
        
        # Create custom fonts
        self.fonts = {
            "heading": (base_font, 16, "bold"),
            "subheading": (base_font, 12, "bold"),
            "default": (base_font, 10),
            "small": (base_font, 9),
            "tiny": (base_font, 8),
            "mono": (mono_font, 10),
            "mono_bold": (mono_font, 10, "bold"),
            "mono_large": (mono_font, 12),
            "status": (base_font, 9, "italic")
        }

    def init_sound(self):
        """Initialize sound effects if pygame is available"""
        if not HAS_SOUND:
            return
            
        try:
            pygame.mixer.init()
            self.sound_initialized = True
            self.sound_enabled = self.settings["sound_enabled"]
            
            # Load sound profiles
            self.sound_profiles = {
                "mechanical": {
                    "description": "Loud mechanical keyboard with clicky switches",
                    "sounds": {}
                },
                "standard": {
                    "description": "Standard office keyboard",
                    "sounds": {}
                },
                "soft": {
                    "description": "Quiet laptop-style keys",
                    "sounds": {}
                },
                "quiet": {
                    "description": "Very soft, dampened keys for stealth",
                    "sounds": {}
                }
            }
            
            # Check for sound files
            sound_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
            if not os.path.exists(sound_dir):
                # Create sounds directory for future use
                try:
                    os.makedirs(sound_dir, exist_ok=True)
                except:
                    pass
            
            # If no sound files exist, we'll use procedurally generated sounds
            self.generate_sound_profiles()
            
        except Exception as e:
            print(f"Error initializing sound: {e}")
            self.sound_initialized = False
            self.sound_enabled = False

    def generate_sound_profiles(self):
        """Generate procedural sound effects for typing"""
        if not self.sound_initialized:
            return
            
        # For each profile, create different keyboard sounds
        for profile_name, profile in self.sound_profiles.items():
            try:
                # Key press sound
                frequency = 0
                duration = 0
                volume = 0
                
                if profile_name == "mechanical":
                    frequency = 2200
                    duration = 30
                    volume = 0.6
                elif profile_name == "standard":
                    frequency = 1800
                    duration = 20
                    volume = 0.4
                elif profile_name == "soft":
                    frequency = 1400
                    duration = 15
                    volume = 0.25
                elif profile_name == "quiet":
                    frequency = 1200
                    duration = 10
                    volume = 0.15
                
                # Create basic key press sound
                key_press_sound = self.generate_key_sound(frequency, duration, volume)
                profile["sounds"]["key"] = key_press_sound
                
                # Create space key sound (slightly different)
                space_sound = self.generate_key_sound(frequency-200, duration+5, volume)
                profile["sounds"]["space"] = space_sound
                
                # Create return key sound (more pronounced)
                return_sound = self.generate_key_sound(frequency-400, duration+10, volume+0.1)
                profile["sounds"]["return"] = return_sound
                
                # Create modifier key sound
                modifier_sound = self.generate_key_sound(frequency+200, duration+5, volume)
                profile["sounds"]["modifier"] = modifier_sound
                
            except Exception as e:
                print(f"Error generating sound profile {profile_name}: {e}")

    def generate_key_sound(self, frequency, duration, volume):
        """Generate a keyboard key sound using pygame"""
        if not self.sound_initialized:
            return None
            
        try:
            # Create an array for a short beep sound
            sample_rate = 44100
            n_samples = int(sample_rate * duration / 1000)
            
            # Create a sound buffer
            buf = bytearray(n_samples)
            
            # Fill with square wave
            for i in range(n_samples):
                if ((i * frequency) // sample_rate) % 2:
                    buf[i] = int(127 + 127 * volume)
                else:
                    buf[i] = int(127 - 127 * volume)
            
            # Create sound object
            sound = pygame.mixer.Sound(bytes(buf))
            
            # Apply fade out
            sound.fadeout(10)
            
            return sound
            
        except Exception as e:
            print(f"Error generating key sound: {e}")
            return None

    def play_key_sound(self, key_type="key"):
        """Play a key sound effect"""
        if not self.sound_initialized or not self.sound_enabled:
            return
            
        try:
            # Get the current profile's sound profile
            sound_profile = self.active_profile.get("sound_profile", "standard")
            if sound_profile not in self.sound_profiles:
                sound_profile = "standard"
                
            # Get the appropriate sound for the key type
            if key_type not in self.sound_profiles[sound_profile]["sounds"]:
                key_type = "key"
                
            sound = self.sound_profiles[sound_profile]["sounds"].get(key_type)
            if sound:
                sound.set_volume(self.settings["sound_volume"])
                sound.play()
        except Exception as e:
            pass  # Silently ignore sound errors during typing

    def create_gui(self):
        """Create the enhanced GUI"""
        # Set up main container with padding
        main_container = ttk.Frame(self.root, style='TFrame', padding=12)
        main_container.pack(fill="both", expand=True)
        
        # Create header with title and main controls
        self.create_header(main_container)
        
        # Main content area
        content = ttk.Frame(main_container, style='TFrame')
        content.pack(fill="both", expand=True, pady=10)
        
        # Create the tabbed interface
        notebook = ttk.Notebook(content)
        notebook.pack(fill="both", expand=True)
        
        # Create tabs
        typing_tab = ttk.Frame(notebook, style='TFrame', padding=10)
        settings_tab = ttk.Frame(notebook, style='TFrame', padding=10)
        profiles_tab = ttk.Frame(notebook, style='TFrame', padding=10)
        about_tab = ttk.Frame(notebook, style='TFrame', padding=10)
        
        notebook.add(typing_tab, text="Typing")
        notebook.add(profiles_tab, text="Profiles")
        notebook.add(settings_tab, text="Settings")
        notebook.add(about_tab, text="About")
        
        # Setup each tab
        self.setup_typing_tab(typing_tab)
        self.setup_profiles_tab(profiles_tab)
        self.setup_settings_tab(settings_tab)
        self.setup_about_tab(about_tab)
        
        # Create status bar
        self.create_status_bar(main_container)
        
        # Apply special effects and styling
        self.apply_ui_effects()
        
        # Adjust the window based on settings
        if self.settings["always_on_top"]:
            self.root.attributes("-topmost", True)

    def create_header(self, parent):
        """Create application header with controls"""
        # Header container with elevated appearance
        header_frame = ttk.Frame(parent, style='Card.TFrame', padding=(15, 10))
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Left side: Logo and title
        title_frame = ttk.Frame(header_frame, style='Card.TFrame')
        title_frame.pack(side="left")
        
        # Attempt to create logo if PIL is available
        if HAS_PIL:
            try:
                # Create a simple logo
                logo_size = 32
                logo_img = Image.new('RGBA', (logo_size, logo_size), (0, 0, 0, 0))
                logo_draw = ImageDraw.Draw(logo_img)
                
                # Draw a keyboard-like icon with accent color
                accent_color_rgb = self.hex_to_rgb(self.colors["accent_primary"])
                background_color_rgb = self.hex_to_rgb(self.colors["card_bg"])
                
                # Draw background circle
                logo_draw.ellipse((0, 0, logo_size, logo_size), fill=background_color_rgb)
                
                # Draw keyboard outline
                padding = 6
                logo_draw.rectangle(
                    (padding, padding+2, logo_size-padding, logo_size-padding-2), 
                    outline=accent_color_rgb, 
                    width=2
                )
                
                # Draw keys
                key_y = logo_size//2
                key_spacing = (logo_size-2*padding) // 4
                for i in range(4):
                    x = padding + i*key_spacing + key_spacing//2
                    logo_draw.rectangle((x-2, key_y-2, x+2, key_y+2), fill=accent_color_rgb)
                
                # Convert to PhotoImage
                logo_tk = ImageTk.PhotoImage(logo_img)
                
                # Display logo
                logo_label = ttk.Label(title_frame, image=logo_tk, style='Card.TLabel')
                logo_label.image = logo_tk  # Keep a reference
                logo_label.pack(side="left", padx=(0, 8))
            except:
                pass
        
        # App title with version
        title_label = ttk.Label(
            title_frame, 
            text=f"Stealth Auto-Typer",
            font=self.fonts["heading"],
            style='Card.TLabel'
        )
        title_label.pack(side="left")
        
        version_label = ttk.Label(
            title_frame, 
            text=f"v{self.version}",
            font=self.fonts["small"],
            foreground=self.colors["fg_tertiary"],
            style='Card.TLabel'
        )
        version_label.pack(side="left", padx=(5, 0), pady=(5, 0))
        
        # Right side: Controls
        controls_frame = ttk.Frame(header_frame, style='Card.TFrame')
        controls_frame.pack(side="right")
        
        # Theme selector
        theme_frame = ttk.Frame(controls_frame, style='Card.TFrame')
        theme_frame.pack(side="left", padx=(0, 15))
        
        theme_label = ttk.Label(
            theme_frame, 
            text="Theme:",
            style='Card.TLabel'
        )
        theme_label.pack(side="left", padx=(0, 5))
        
        self.theme_var = tk.StringVar(value=self.theme_mode)
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=["light", "dark", "amoled"],
            width=8,
            state="readonly"
        )
        theme_combo.pack(side="left")
        theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        
        # Sound toggle
        self.sound_var = tk.BooleanVar(value=self.sound_enabled)
        sound_cb = ttk.Checkbutton(
            controls_frame,
            text="Sound Effects",
            variable=self.sound_var,
            style='Card.TCheckbutton',
            command=self.toggle_sound
        )
        sound_cb.pack(side="left", padx=10)
        
        # Always on top toggle
        self.always_on_top_var = tk.BooleanVar(value=self.settings["always_on_top"])
        always_on_top_cb = ttk.Checkbutton(
            controls_frame,
            text="Always on Top",
            variable=self.always_on_top_var,
            style='Card.TCheckbutton',
            command=self.toggle_always_on_top
        )
        always_on_top_cb.pack(side="left", padx=10)
        
        # Mini panel toggle
        self.mini_panel_var = tk.BooleanVar(value=self.settings["mini_panel_enabled"])
        mini_panel_cb = ttk.Checkbutton(
            controls_frame,
            text="Mini Panel",
            variable=self.mini_panel_var,
            style='Card.TCheckbutton',
            command=self.toggle_mini_panel
        )
        mini_panel_cb.pack(side="left", padx=10)

    def setup_typing_tab(self, parent):
        """Set up the main typing tab with card layout"""
        # Text input card
        input_card = self.create_card(parent, "Text to Type")
        input_card.pack(fill="both", expand=True, pady=(0, 10))
        
        # Text tools in a horizontal buttonbar
        tools_frame = ttk.Frame(input_card, style='Card.TFrame')
        tools_frame.pack(fill="x", pady=(0, 8))
        
        # File operations
        file_frame = ttk.Frame(tools_frame, style='Card.TFrame')
        file_frame.pack(side="left")
        
        # Create toolbar buttons with icons if PIL is available
        if HAS_PIL:
            # Try to create simple icons
            icon_size = 16
            icon_bg = self.colors["bg_tertiary"]
            icon_fg = self.colors["fg_primary"]
            
            # Load file icon
            try:
                load_icon = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(load_icon)
                draw.rectangle((2, 4, 14, 14), outline=icon_fg, width=1)
                draw.polygon([(4, 4), (8, 1), (12, 4)], fill=icon_fg)
                load_icon_tk = ImageTk.PhotoImage(load_icon)
            except:
                load_icon_tk = None
                
            # Save file icon
            try:
                save_icon = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(save_icon)
                draw.rectangle((2, 2, 14, 14), outline=icon_fg, width=1)
                draw.rectangle((4, 8, 12, 12), fill=icon_fg)
                save_icon_tk = ImageTk.PhotoImage(save_icon)
            except:
                save_icon_tk = None
                
            # Clear icon
            try:
                clear_icon = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(clear_icon)
                draw.line((3, 3, 13, 13), fill=icon_fg, width=2)
                draw.line((3, 13, 13, 3), fill=icon_fg, width=2)
                clear_icon_tk = ImageTk.PhotoImage(clear_icon)
            except:
                clear_icon_tk = None
            
            # Create buttons with icons
            load_btn = ttk.Button(
                file_frame,
                text=" Load File" if load_icon_tk else "Load File",
                image=load_icon_tk if load_icon_tk else None,
                compound="left" if load_icon_tk else "none",
                command=self.load_from_file
            )
            load_btn.image = load_icon_tk  # Keep a reference
            load_btn.pack(side="left", padx=(0, 4))
            
            save_btn = ttk.Button(
                file_frame,
                text=" Save" if save_icon_tk else "Save",
                image=save_icon_tk if save_icon_tk else None,
                compound="left" if save_icon_tk else "none",
                command=self.save_to_file
            )
            save_btn.image = save_icon_tk  # Keep a reference
            save_btn.pack(side="left", padx=4)
            
            clear_btn = ttk.Button(
                file_frame,
                text=" Clear" if clear_icon_tk else "Clear",
                image=clear_icon_tk if clear_icon_tk else None,
                compound="left" if clear_icon_tk else "none",
                command=lambda: self.text_input.delete("1.0", tk.END)
            )
            clear_btn.image = clear_icon_tk  # Keep a reference
            clear_btn.pack(side="left", padx=4)
        else:
            # Fallback to text-only buttons
            ttk.Button(
                file_frame,
                text="Load File",
                command=self.load_from_file
            ).pack(side="left", padx=(0, 4))
            
            ttk.Button(
                file_frame,
                text="Save",
                command=self.save_to_file
            ).pack(side="left", padx=4)
            
            ttk.Button(
                file_frame,
                text="Clear",
                command=lambda: self.text_input.delete("1.0", tk.END)
            ).pack(side="left", padx=4)
        
        # Quick settings on the right
        settings_frame = ttk.Frame(tools_frame, style='Card.TFrame')
        settings_frame.pack(side="right")
        
        # Font size control
        font_frame = ttk.Frame(settings_frame, style='Card.TFrame')
        font_frame.pack(side="left", padx=(0, 10))
        
        font_label = ttk.Label(
            font_frame, 
            text="Font Size:",
            style='Card.TLabel'
        )
        font_label.pack(side="left", padx=(0, 5))
        
        self.font_size_var = tk.IntVar(value=11)
        font_spin = ttk.Spinbox(
            font_frame,
            from_=8,
            to=16,
            textvariable=self.font_size_var,
            width=2,
            command=self.update_font_size
        )
        font_spin.pack(side="left")
        
        # Clipboard paste button
        ttk.Button(
            settings_frame,
            text="Paste from Clipboard",
            command=self.paste_from_clipboard
        ).pack(side="left")
        
        # Text input area with syntax highlighting
        self.text_input = scrolledtext.ScrolledText(
            input_card,
            wrap=tk.WORD,
            bg=self.colors["bg_input"],
            fg=self.colors["fg_primary"],
            insertbackground=self.colors["fg_primary"],
            height=12,
            font=self.fonts["mono"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0
        )
        self.text_input.pack(fill="both", expand=True, pady=5)
        
        # Typing controls card
        controls_card = self.create_card(parent, "Typing Controls")
        controls_card.pack(fill="x", pady=10)
        
        # Profile selector
        profile_frame = ttk.Frame(controls_card, style='Card.TFrame')
        profile_frame.pack(fill="x", pady=(0, 10))
        
        profile_label = ttk.Label(
            profile_frame, 
            text="Typing Profile:",
            style='Card.TLabel'
        )
        profile_label.pack(side="left", padx=(0, 5))
        
        self.profile_var = tk.StringVar(value=self.current_profile)
        self.profile_combo = ttk.Combobox(
            profile_frame,
            textvariable=self.profile_var,
            values=list(self.typing_profiles.keys()),
            width=15,
            state="readonly"
        )
        self.profile_combo.pack(side="left")
        self.profile_combo.bind("<<ComboboxSelected>>", self.update_profile)
        
        # Profile description
        self.profile_desc_var = tk.StringVar(
            value=self.typing_profiles[self.current_profile]["description"]
        )
        profile_desc = ttk.Label(
            profile_frame,
            textvariable=self.profile_desc_var,
            style='Card.TLabel',
            font=self.fonts["small"]
        )
        profile_desc.pack(side="left", padx=10)
        
        # Apply profile button
        ttk.Button(
            profile_frame,
            text="Apply",
            command=self.apply_profile,
            style='Accent.TButton',
            width=8
        ).pack(side="right", padx=5)
        
        # Control panels - using grid layout
        controls_grid = ttk.Frame(controls_card, style='Card.TFrame')
        controls_grid.pack(fill="x", pady=5)
        
        # Split controls into two columns
        left_controls = ttk.Frame(controls_grid, style='Card.TFrame')
        left_controls.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        right_controls = ttk.Frame(controls_grid, style='Card.TFrame')
        right_controls.grid(row=0, column=1, sticky="nsew")
        
        # Configure grid weights
        controls_grid.columnconfigure(0, weight=1)
        controls_grid.columnconfigure(1, weight=1)
        
        # Left controls: Speed settings
        # WPM control
        wpm_frame = ttk.Frame(left_controls, style='Card.TFrame')
        wpm_frame.pack(fill="x", pady=2)
        
        wpm_label = ttk.Label(
            wpm_frame, 
            text="Typing Speed:",
            style='Card.TLabel',
            width=12
        )
        wpm_label.pack(side="left")
        
        self.wpm_var = tk.IntVar(value=self.active_profile["base_wpm"])
        self.wpm_slider = ttk.Scale(
            wpm_frame,
            from_=20,
            to=200,
            orient="horizontal",
            variable=self.wpm_var,
            command=self.update_wpm_display
        )
        self.wpm_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.wpm_label = ttk.Label(
            wpm_frame, 
            text=f"{self.wpm_var.get()} WPM",
            style='Card.TLabel',
            width=8
        )
        self.wpm_label.pack(side="left")
        
        # Variation control
        var_frame = ttk.Frame(left_controls, style='Card.TFrame')
        var_frame.pack(fill="x", pady=2)
        
        var_label = ttk.Label(
            var_frame, 
            text="Speed Variation:",
            style='Card.TLabel',
            width=12
        )
        var_label.pack(side="left")
        
        self.variation_var = tk.IntVar(value=self.active_profile["wpm_variation"])
        self.variation_slider = ttk.Scale(
            var_frame,
            from_=0,
            to=50,
            orient="horizontal",
            variable=self.variation_var,
            command=self.update_variation_display
        )
        self.variation_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.variation_label = ttk.Label(
            var_frame, 
            text=f"±{self.variation_var.get()}%",
            style='Card.TLabel',
            width=8
        )
        self.variation_label.pack(side="left")
        
        # Error rate control
        error_frame = ttk.Frame(left_controls, style='Card.TFrame')
        error_frame.pack(fill="x", pady=2)
        
        error_label = ttk.Label(
            error_frame, 
            text="Error Rate:",
            style='Card.TLabel',
            width=12
        )
        error_label.pack(side="left")
        
        self.error_rate_var = tk.DoubleVar(value=self.active_profile["error_rate"])
        self.error_slider = ttk.Scale(
            error_frame,
            from_=0,
            to=10,
            orient="horizontal",
            variable=self.error_rate_var,
            command=self.update_error_display
        )
        self.error_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.error_label = ttk.Label(
            error_frame, 
            text=f"{self.error_rate_var.get():.1f}%",
            style='Card.TLabel',
            width=8
        )
        self.error_label.pack(side="left")
        
        # Right controls: Humanization options
        # Checkboxes for typing options
        options_frame = ttk.Frame(right_controls, style='Card.TFrame')
        options_frame.pack(fill="x", pady=2)
        
        # Smart pauses option
        self.smart_pauses_var = tk.BooleanVar(value=self.active_profile["smart_pauses"])
        smart_pauses_cb = ttk.Checkbutton(
            options_frame,
            text="Smart Pauses",
            variable=self.smart_pauses_var,
            style='Card.TCheckbutton'
        )
        smart_pauses_cb.pack(anchor="w", pady=1)
        
        # Word bursts option
        self.word_burst_var = tk.BooleanVar(value=self.active_profile["word_burst"])
        word_burst_cb = ttk.Checkbutton(
            options_frame,
            text="Word Bursts",
            variable=self.word_burst_var,
            style='Card.TCheckbutton'
        )
        word_burst_cb.pack(anchor="w", pady=1)
        
        # Thought pauses option (only for Ultra Stealth profile)
        self.thought_pause_var = tk.BooleanVar(
            value=self.active_profile.get("thought_pause_probability", 0) > 0
        )
        thought_pause_cb = ttk.Checkbutton(
            options_frame,
            text="Random Thought Pauses",
            variable=self.thought_pause_var,
            style='Card.TCheckbutton'
        )
        thought_pause_cb.pack(anchor="w", pady=1)
        
        # Typing rhythm selection
        rhythm_frame = ttk.Frame(right_controls, style='Card.TFrame')
        rhythm_frame.pack(fill="x", pady=(5, 2))
        
        rhythm_label = ttk.Label(
            rhythm_frame, 
            text="Typing Rhythm:",
            style='Card.TLabel'
        )
        rhythm_label.pack(side="left", padx=(0, 5))
        
        self.rhythm_var = tk.StringVar(value=self.active_profile["typing_rhythm"])
        rhythm_combo = ttk.Combobox(
            rhythm_frame,
            textvariable=self.rhythm_var,
            values=["natural", "consistent", "irregular", "ultra_natural"],
            width=15,
            state="readonly"
        )
        rhythm_combo.pack(side="left", fill="x", expand=True)
        
        # Countdown spinner
        countdown_frame = ttk.Frame(right_controls, style='Card.TFrame')
        countdown_frame.pack(fill="x", pady=(10, 2))
        
        countdown_label = ttk.Label(
            countdown_frame, 
            text="Start Countdown:",
            style='Card.TLabel'
        )
        countdown_label.pack(side="left", padx=(0, 5))
        
        self.countdown_var = tk.IntVar(value=3)
        countdown_spin = ttk.Spinbox(
            countdown_frame,
            from_=0,
            to=10,
            textvariable=self.countdown_var,
            width=3
        )
        countdown_spin.pack(side="left")
        
        ttk.Label(
            countdown_frame, 
            text="seconds",
            style='Card.TLabel'
        ).pack(side="left", padx=5)
        
        # Action buttons with enhanced styling
        action_frame = ttk.Frame(controls_card, style='Card.TFrame')
        action_frame.pack(fill="x", pady=(10, 0))
        
        # Start button
        self.start_btn = ttk.Button(
            action_frame,
            text="Start Typing",
            style='Success.TButton',
            command=self.start_typing
        )
        self.start_btn.pack(side="left", padx=(0, 5))
        
        # Add hotkey hint
        start_hotkey = ttk.Label(
            action_frame,
            text=f"({self.settings['hotkeys']['start_typing']})",
            style='Card.TLabel',
            font=self.fonts["small"]
        )
        start_hotkey.pack(side="left", padx=(0, 15))
        
        # Pause button
        self.pause_btn = ttk.Button(
            action_frame,
            text="Pause",
            command=self.toggle_pause,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=5)
        
        # Add hotkey hint
        pause_hotkey = ttk.Label(
            action_frame,
            text=f"({self.settings['hotkeys']['pause_typing']})",
            style='Card.TLabel',
            font=self.fonts["small"]
        )
        pause_hotkey.pack(side="left", padx=(0, 15))
        
        # Stop button
        self.stop_btn = ttk.Button(
            action_frame,
            text="Stop",
            style='Error.TButton',
            command=self.stop_typing,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # Add hotkey hint
        stop_hotkey = ttk.Label(
            action_frame,
            text=f"({self.settings['hotkeys']['stop_typing']})",
            style='Card.TLabel',
            font=self.fonts["small"]
        )
        stop_hotkey.pack(side="left")
        
        # Progress card
        progress_card = self.create_card(parent, "Status & Preview")
        progress_card.pack(fill="x", pady=(10, 0))
        
        # Progress bar with label
        progress_frame = ttk.Frame(progress_card, style='Card.TFrame')
        progress_frame.pack(fill="x", pady=(0, 8))
        
        progress_label = ttk.Label(
            progress_frame, 
            text="Progress:",
            style='Card.TLabel'
        )
        progress_label.pack(side="left", padx=(0, 5))
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            length=300,
            mode="determinate",
            variable=self.progress_var
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        
        self.progress_label = ttk.Label(
            progress_frame, 
            text="0/0 chars",
            style='Card.TLabel'
        )
        self.progress_label.pack(side="left", padx=5)
        
        # Status and typing info section
        status_frame = ttk.Frame(progress_card, style='Card.TFrame')
        status_frame.pack(fill="x", pady=2)
        
        # Typing status with indicator
        status_indicator_frame = ttk.Frame(status_frame, style='Card.TFrame')
        status_indicator_frame.pack(side="left")
        
        # Status label
        status_label = ttk.Label(
            status_indicator_frame, 
            text="Status:",
            style='Card.TLabel'
        )
        status_label.pack(side="left")
        
        # Status indicator (colored circle)
        self.status_indicator = tk.Canvas(
            status_indicator_frame,
            width=12,
            height=12,
            bg=self.colors["card_bg"],
            highlightthickness=0
        )
        self.status_indicator.pack(side="left", padx=5)
        
        # Draw status circle
        self.status_circle = self.status_indicator.create_oval(2, 2, 10, 10, fill=self.colors["success"])
        
        # Status text
        self.status_var = tk.StringVar(value="Ready")
        status_text = ttk.Label(
            status_indicator_frame,
            textvariable=self.status_var,
            style='Card.TLabel',
            font=self.fonts["subheading"]
        )
        status_text.pack(side="left", padx=5)
        
        # Current WPM display (right side)
        self.current_wpm_var = tk.StringVar(value="0 WPM")
        current_wpm = ttk.Label(
            status_frame,
            textvariable=self.current_wpm_var,
            style='Card.TLabel',
            font=self.fonts["subheading"]
        )
        current_wpm.pack(side="right", padx=5)
        
        current_wpm_label = ttk.Label(
            status_frame,
            text="Current Speed:",
            style='Card.TLabel'
        )
        current_wpm_label.pack(side="right")
        
        # Typing preview with animation
        preview_frame = ttk.Frame(progress_card, style='Card.TFrame')
        preview_frame.pack(fill="x", pady=(8, 0))
        
        preview_label = ttk.Label(
            preview_frame, 
            text="Preview:",
            style='Card.TLabel'
        )
        preview_label.pack(side="left", padx=(0, 5))
        
        # Create a text widget for more formatting control
        self.preview_text = tk.Text(
            preview_frame,
            height=1,
            bg=self.colors["bg_input"],
            fg=self.colors["fg_primary"],
            insertbackground=self.colors["fg_primary"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=self.fonts["mono"],
            padx=10,
            pady=5,
            wrap="none"
        )
        self.preview_text.pack(fill="x", expand=True, padx=5)
        self.preview_text.insert("1.0", "No text to type")
        self.preview_text.config(state="disabled")
        
        # Create preview cursor
        self.preview_text.tag_configure("cursor", background=self.colors["accent_primary"])
        self.preview_text.tag_configure("typed", foreground=self.colors["accent_secondary"])
        self.preview_text.tag_configure("untyped", foreground=self.colors["fg_secondary"])

    def setup_profiles_tab(self, parent):
        """Set up profiles tab for managing typing profiles"""
        # Profiles card
        profiles_card = self.create_card(parent, "Typing Profiles")
        profiles_card.pack(fill="both", expand=True, pady=(0, 10))
        
        # Top controls for profile management
        controls_frame = ttk.Frame(profiles_card, style='Card.TFrame')
        controls_frame.pack(fill="x", pady=(0, 10))
        
        # New profile button
        ttk.Button(
            controls_frame,
            text="New Profile",
            command=self.create_new_profile
        ).pack(side="left", padx=(0, 5))
        
        # Clone current profile
        ttk.Button(
            controls_frame,
            text="Clone Selected",
            command=self.clone_profile
        ).pack(side="left", padx=5)
        
        # Delete profile
        ttk.Button(
            controls_frame,
            text="Delete Profile",
            command=self.delete_profile
        ).pack(side="left", padx=5)
        
        # Import/Export
        ttk.Button(
            controls_frame,
            text="Export Profiles",
            command=self.export_profiles
        ).pack(side="right")
        
        ttk.Button(
            controls_frame,
            text="Import Profiles",
            command=self.import_profiles
        ).pack(side="right", padx=5)
        
        # Create a frame with two panes: profile list and settings
        panes_frame = ttk.Frame(profiles_card, style='Card.TFrame')
        panes_frame.pack(fill="both", expand=True)
        
        # Left pane: Profile list
        list_frame = ttk.Frame(panes_frame, style='Card.TFrame')
        list_frame.pack(side="left", fill="y", padx=(0, 10))
        
        # Profile list header
        ttk.Label(
            list_frame, 
            text="Available Profiles",
            style='Card.TLabel',
            font=self.fonts["subheading"]
        ).pack(anchor="w", pady=(0, 5))
        
        # Profile list
        list_container = ttk.Frame(list_frame, style='TFrame')
        list_container.pack(fill="both", expand=True)
        
        # Create a listbox with scrollbar
        list_scroll = ttk.Scrollbar(list_container)
        list_scroll.pack(side="right", fill="y")
        
        self.profile_list = tk.Listbox(
            list_container,
            bg=self.colors["bg_input"],
            fg=self.colors["fg_primary"],
            selectbackground=self.colors["accent_primary"],
            selectforeground=self.colors["bg_primary"],
            font=self.fonts["default"],
            height=15,
            width=25,
            borderwidth=0,
            highlightthickness=0
        )
        self.profile_list.pack(side="left", fill="both", expand=True)
        
        # Connect scrollbar
        self.profile_list.config(yscrollcommand=list_scroll.set)
        list_scroll.config(command=self.profile_list.yview)
        
        # Populate the list
        for profile in self.typing_profiles:
            self.profile_list.insert(tk.END, profile)
            
        # Select current profile
        current_index = list(self.typing_profiles.keys()).index(self.current_profile)
        self.profile_list.selection_set(current_index)
        self.profile_list.see(current_index)
        
        # Bind selection event
        self.profile_list.bind("<<ListboxSelect>>", self.on_profile_selected)
        
        # Right pane: Profile settings
        settings_frame = ttk.Frame(panes_frame, style='Card.TFrame')
        settings_frame.pack(side="right", fill="both", expand=True)
        
        # Profile settings header
        self.profile_edit_name_var = tk.StringVar(value=self.current_profile)
        self.profile_header = ttk.Label(
            settings_frame, 
            textvariable=self.profile_edit_name_var,
            style='Card.TLabel',
            font=self.fonts["subheading"]
        )
        self.profile_header.pack(anchor="w", pady=(0, 5))
        
        # Create a notebook for profile settings
        profile_notebook = ttk.Notebook(settings_frame)
        profile_notebook.pack(fill="both", expand=True)
        
        # Create tabs for different profile settings
        basic_tab = ttk.Frame(profile_notebook, style='TFrame', padding=10)
        advanced_tab = ttk.Frame(profile_notebook, style='TFrame', padding=10)
        
        profile_notebook.add(basic_tab, text="Basic Settings")
        profile_notebook.add(advanced_tab, text="Advanced Settings")
        
        # Basic settings tab
        self.setup_profile_basic_tab(basic_tab)
        
        # Advanced settings tab
        self.setup_profile_advanced_tab(advanced_tab)
        
        # Save changes button at the bottom
        save_frame = ttk.Frame(settings_frame, style='Card.TFrame')
        save_frame.pack(fill="x", pady=10)
        
        ttk.Button(
            save_frame,
            text="Save Profile Changes",
            style='Accent.TButton',
            command=self.save_profile_changes
        ).pack(side="right")
        
        ttk.Button(
            save_frame,
            text="Discard Changes",
            command=self.discard_profile_changes
        ).pack(side="right", padx=5)

    def setup_profile_basic_tab(self, parent):
        """Set up basic profile settings tab"""
        # Profile name and description
        name_frame = ttk.Frame(parent, style='TFrame')
        name_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            name_frame, 
            text="Profile Name:",
            width=15
        ).pack(side="left")
        
        self.profile_name_var = tk.StringVar(value=self.current_profile)
        name_entry = ttk.Entry(
            name_frame,
            textvariable=self.profile_name_var,
            width=25
        )
        name_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Description
        desc_frame = ttk.Frame(parent, style='TFrame')
        desc_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            desc_frame, 
            text="Description:",
            width=15
        ).pack(side="left")
        
        self.profile_desc_edit_var = tk.StringVar(
            value=self.typing_profiles[self.current_profile]["description"]
        )
        desc_entry = ttk.Entry(
            desc_frame,
            textvariable=self.profile_desc_edit_var
        )
        desc_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Create a separator
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
        
        # Speed settings
        ttk.Label(
            parent, 
            text="Speed Settings",
            font=self.fonts["subheading"]
        ).pack(anchor="w", pady=(0, 5))
        
        # Base WPM
        wpm_frame = ttk.Frame(parent, style='TFrame')
        wpm_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            wpm_frame, 
            text="Base WPM:",
            width=15
        ).pack(side="left")
        
        self.edit_wpm_var = tk.IntVar(value=self.typing_profiles[self.current_profile]["base_wpm"])
        wpm_slider = ttk.Scale(
            wpm_frame,
            from_=20,
            to=200,
            orient="horizontal",
            variable=self.edit_wpm_var
        )
        wpm_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        wpm_label = ttk.Label(
            wpm_frame, 
            textvariable=self.edit_wpm_var,
            width=3
        )
        wpm_label.pack(side="left")
        
        # Variation
        var_frame = ttk.Frame(parent, style='TFrame')
        var_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            var_frame, 
            text="WPM Variation (%):",
            width=15
        ).pack(side="left")
        
        self.edit_var_var = tk.IntVar(
            value=self.typing_profiles[self.current_profile]["wpm_variation"]
        )
        var_slider = ttk.Scale(
            var_frame,
            from_=0,
            to=50,
            orient="horizontal",
            variable=self.edit_var_var
        )
        var_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        var_label = ttk.Label(
            var_frame, 
            textvariable=self.edit_var_var,
            width=3
        )
        var_label.pack(side="left")
        
        # Error rate
        error_frame = ttk.Frame(parent, style='TFrame')
        error_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            error_frame, 
            text="Error Rate (%):",
            width=15
        ).pack(side="left")
        
        self.edit_error_var = tk.DoubleVar(
            value=self.typing_profiles[self.current_profile]["error_rate"]
        )
        error_slider = ttk.Scale(
            error_frame,
            from_=0,
            to=10,
            orient="horizontal",
            variable=self.edit_error_var
        )
        error_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        error_label = ttk.Label(
            error_frame, 
            textvariable=self.edit_error_var,
            width=3
        )
        error_label.pack(side="left")
        
        # Create a separator
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
        
        # Basic options
        ttk.Label(
            parent, 
            text="Typing Behavior",
            font=self.fonts["subheading"]
        ).pack(anchor="w", pady=(0, 5))
        
        # Options grid (2 columns)
        options_frame = ttk.Frame(parent, style='TFrame')
        options_frame.pack(fill="x")
        
        # Configure columns
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        
        # Smart pauses
        self.edit_smart_pauses_var = tk.BooleanVar(
            value=self.typing_profiles[self.current_profile]["smart_pauses"]
        )
        smart_pauses_cb = ttk.Checkbutton(
            options_frame,
            text="Smart Pauses",
            variable=self.edit_smart_pauses_var
        )
        smart_pauses_cb.grid(row=0, column=0, sticky="w", pady=2)
        
        # Word bursts
        self.edit_word_burst_var = tk.BooleanVar(
            value=self.typing_profiles[self.current_profile]["word_burst"]
        )
        word_burst_cb = ttk.Checkbutton(
            options_frame,
            text="Word Bursts",
            variable=self.edit_word_burst_var
        )
        word_burst_cb.grid(row=0, column=1, sticky="w", pady=2)
        
        # Rhythm selection
        rhythm_frame = ttk.Frame(parent, style='TFrame')
        rhythm_frame.pack(fill="x", pady=(10, 2))
        
        ttk.Label(
            rhythm_frame, 
            text="Typing Rhythm:",
            width=15
        ).pack(side="left")
        
        self.edit_rhythm_var = tk.StringVar(
            value=self.typing_profiles[self.current_profile]["typing_rhythm"]
        )
        rhythm_combo = ttk.Combobox(
            rhythm_frame,
            textvariable=self.edit_rhythm_var,
            values=["natural", "consistent", "irregular", "ultra_natural"],
            state="readonly"
        )
        rhythm_combo.pack(side="left", fill="x", expand=True, padx=5)
        
        # Sound profile
        sound_frame = ttk.Frame(parent, style='TFrame')
        sound_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            sound_frame, 
            text="Sound Profile:",
            width=15
        ).pack(side="left")
        
        self.edit_sound_var = tk.StringVar(
            value=self.typing_profiles[self.current_profile].get("sound_profile", "standard")
        )
        sound_combo = ttk.Combobox(
            sound_frame,
            textvariable=self.edit_sound_var,
            values=["mechanical", "standard", "soft", "quiet"],
            state="readonly"
        )
        sound_combo.pack(side="left", fill="x", expand=True, padx=5)

    def setup_profile_advanced_tab(self, parent):
        """Set up advanced profile settings tab"""
        # Pause multipliers section
        ttk.Label(
            parent, 
            text="Pause Multipliers",
            font=self.fonts["subheading"]
        ).pack(anchor="w", pady=(0, 5))
        
        # Help text
        ttk.Label(
            parent, 
            text="These multipliers determine how long the typing pauses after specific characters.",
            wraplength=400,
            foreground=self.colors["fg_secondary"]
        ).pack(anchor="w", pady=(0, 5))
        
        # Create a frame for the multipliers grid
        multi_frame = ttk.Frame(parent, style='TFrame')
        multi_frame.pack(fill="x", pady=5)
        
        # Configure grid
        for i in range(4):  # 4 columns
            multi_frame.columnconfigure(i, weight=1)
            
        # Get current multipliers
        current_multipliers = self.typing_profiles[self.current_profile]["pause_multiplier"]
        
        # Create variables for each multiplier
        self.multiplier_vars = {}
        
        # Add sliders for each punctuation with its multiplier
        row = 0
        col = 0
        for char, multiplier in sorted(current_multipliers.items()):
            # Skip newline and tab for separate handling
            if char in ["\n", "\t"]:
                continue
                
            # Create a frame for this multiplier
            char_frame = ttk.Frame(multi_frame, style='TFrame')
            char_frame.grid(row=row, column=col, sticky="ew", padx=5, pady=2)
            
            # Character display (properly escaped)
            char_display = char
            if char == "\n":
                char_display = "\\n"
            elif char == "\t":
                char_display = "\\t"
                
            ttk.Label(
                char_frame, 
                text=f"'{char_display}':",
                width=4
            ).pack(side="left")
            
            # Create variable
            self.multiplier_vars[char] = tk.DoubleVar(value=multiplier)
            
            # Create slider
            char_slider = ttk.Scale(
                char_frame,
                from_=1.0,
                to=5.0,
                orient="horizontal",
                variable=self.multiplier_vars[char]
            )
            char_slider.pack(side="left", fill="x", expand=True, padx=2)
            
            # Value label
            value_label = ttk.Label(
                char_frame, 
                textvariable=self.multiplier_vars[char],
                width=3
            )
            value_label.pack(side="left")
            
            # Move to next column or row
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        # Add special characters in their own section
        ttk.Label(
            parent, 
            text="Special Characters",
            font=self.fonts["small"],
            padding=(0, 10, 0, 5)
        ).pack(anchor="w")
        
        # Frame for special character multipliers
        special_frame = ttk.Frame(parent, style='TFrame')
        special_frame.pack(fill="x", pady=2)
        
        # Configure columns
        special_frame.columnconfigure(0, weight=1)
        special_frame.columnconfigure(1, weight=1)
        
        # Newline
        nl_frame = ttk.Frame(special_frame, style='TFrame')
        nl_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        
        ttk.Label(
            nl_frame, 
            text="'\\n' (Enter):",
            width=10
        ).pack(side="left")
        
        self.multiplier_vars["\n"] = tk.DoubleVar(value=current_multipliers.get("\n", 4.0))
        
        nl_slider = ttk.Scale(
            nl_frame,
            from_=1.0,
            to=6.0,
            orient="horizontal",
            variable=self.multiplier_vars["\n"]
        )
        nl_slider.pack(side="left", fill="x", expand=True, padx=2)
        
        nl_label = ttk.Label(
            nl_frame, 
            textvariable=self.multiplier_vars["\n"],
            width=3
        )
        nl_label.pack(side="left")
        
        # Tab
        tab_frame = ttk.Frame(special_frame, style='TFrame')
        tab_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(
            tab_frame, 
            text="'\\t' (Tab):",
            width=10
        ).pack(side="left")
        
        self.multiplier_vars["\t"] = tk.DoubleVar(value=current_multipliers.get("\t", 2.0))
        
        tab_slider = ttk.Scale(
            tab_frame,
            from_=1.0,
            to=5.0,
            orient="horizontal",
            variable=self.multiplier_vars["\t"]
        )
        tab_slider.pack(side="left", fill="x", expand=True, padx=2)
        
        tab_label = ttk.Label(
            tab_frame, 
            textvariable=self.multiplier_vars["\t"],
            width=3
        )
        tab_label.pack(side="left")
        
        # Create a separator
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
        
        # Word burst settings
        ttk.Label(
            parent, 
            text="Word Burst Settings",
            font=self.fonts["subheading"]
        ).pack(anchor="w", pady=(0, 5))
        
        # Help text
        ttk.Label(
            parent, 
            text="Control how word bursts behave when typing common words.",
            wraplength=400,
            foreground=self.colors["fg_secondary"]
        ).pack(anchor="w", pady=(0, 5))
        
        # Burst probability
        burst_prob_frame = ttk.Frame(parent, style='TFrame')
        burst_prob_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            burst_prob_frame, 
            text="Burst Probability:",
            width=15
        ).pack(side="left")
        
        self.edit_burst_prob_var = tk.DoubleVar(
            value=self.typing_profiles[self.current_profile]["burst_probability"]
        )
        burst_prob_slider = ttk.Scale(
            burst_prob_frame,
            from_=0.0,
            to=1.0,
            orient="horizontal",
            variable=self.edit_burst_prob_var
        )
        burst_prob_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        # Format probability as percentage
        burst_prob_formatted = tk.StringVar(value=f"{self.edit_burst_prob_var.get()*100:.0f}%")
        
        def update_burst_prob(*args):
            burst_prob_formatted.set(f"{self.edit_burst_prob_var.get()*100:.0f}%")
            
        self.edit_burst_prob_var.trace_add("write", update_burst_prob)
        
        burst_prob_label = ttk.Label(
            burst_prob_frame, 
            textvariable=burst_prob_formatted,
            width=5
        )
        burst_prob_label.pack(side="left")
        
        # Burst speed multiplier
        burst_speed_frame = ttk.Frame(parent, style='TFrame')
        burst_speed_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            burst_speed_frame, 
            text="Burst Speed Boost:",
            width=15
        ).pack(side="left")
        
        self.edit_burst_speed_var = tk.DoubleVar(
            value=self.typing_profiles[self.current_profile]["burst_speed_multiplier"]
        )
        burst_speed_slider = ttk.Scale(
            burst_speed_frame,
            from_=1.0,
            to=2.0,
            orient="horizontal",
            variable=self.edit_burst_speed_var
        )
        burst_speed_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        # Format multiplier with x
        burst_speed_formatted = tk.StringVar(value=f"{self.edit_burst_speed_var.get():.1f}x")
        
        def update_burst_speed(*args):
            burst_speed_formatted.set(f"{self.edit_burst_speed_var.get():.1f}x")
            
        self.edit_burst_speed_var.trace_add("write", update_burst_speed)
        
        burst_speed_label = ttk.Label(
            burst_speed_frame, 
            textvariable=burst_speed_formatted,
            width=5
        )
        burst_speed_label.pack(side="left")
        
        # Create a separator
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
        
        # Thought pause settings (Ultra Stealth feature)
        ttk.Label(
            parent, 
            text="Thought Pause Settings",
            font=self.fonts["subheading"]
        ).pack(anchor="w", pady=(0, 5))
        
        # Help text
        ttk.Label(
            parent, 
            text="These settings control random pauses mimicking a human thinking while typing.",
            wraplength=400,
            foreground=self.colors["fg_secondary"]
        ).pack(anchor="w", pady=(0, 5))
        
        # Enable thought pauses
        thought_enable_frame = ttk.Frame(parent, style='TFrame')
        thought_enable_frame.pack(fill="x", pady=2)
        
        self.edit_thought_enable_var = tk.BooleanVar(
            value=self.typing_profiles[self.current_profile].get("thought_pause_probability", 0) > 0
        )
        thought_enable_cb = ttk.Checkbutton(
            thought_enable_frame,
            text="Enable Random Thought Pauses",
            variable=self.edit_thought_enable_var
        )
        thought_enable_cb.pack(anchor="w")
        
        # Thought pause probability
        thought_prob_frame = ttk.Frame(parent, style='TFrame')
        thought_prob_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            thought_prob_frame, 
            text="Pause Probability:",
            width=15
        ).pack(side="left")
        
        self.edit_thought_prob_var = tk.DoubleVar(
            value=self.typing_profiles[self.current_profile].get("thought_pause_probability", 0.08)
        )
        thought_prob_slider = ttk.Scale(
            thought_prob_frame,
            from_=0.01,
            to=0.2,
            orient="horizontal",
            variable=self.edit_thought_prob_var
        )
        thought_prob_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        # Format probability as percentage
        thought_prob_formatted = tk.StringVar(value=f"{self.edit_thought_prob_var.get()*100:.1f}%")
        
        def update_thought_prob(*args):
            thought_prob_formatted.set(f"{self.edit_thought_prob_var.get()*100:.1f}%")
            
        self.edit_thought_prob_var.trace_add("write", update_thought_prob)
        
        thought_prob_label = ttk.Label(
            thought_prob_frame, 
            textvariable=thought_prob_formatted,
            width=5
        )
        thought_prob_label.pack(side="left")
        
        # Pause duration range
        # Min duration
        min_dur_frame = ttk.Frame(parent, style='TFrame')
        min_dur_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            min_dur_frame, 
            text="Min Duration (s):",
            width=15
        ).pack(side="left")
        
        default_durations = self.typing_profiles[self.current_profile].get(
            "thought_pause_duration", (0.8, 3.0)
        )
        
        self.edit_min_dur_var = tk.DoubleVar(value=default_durations[0])
        min_dur_slider = ttk.Scale(
            min_dur_frame,
            from_=0.2,
            to=2.0,
            orient="horizontal",
            variable=self.edit_min_dur_var
        )
        min_dur_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        min_dur_label = ttk.Label(
            min_dur_frame, 
            textvariable=self.edit_min_dur_var,
            width=5
        )
        min_dur_label.pack(side="left")
        
        # Max duration
        max_dur_frame = ttk.Frame(parent, style='TFrame')
        max_dur_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            max_dur_frame, 
            text="Max Duration (s):",
            width=15
        ).pack(side="left")
        
        self.edit_max_dur_var = tk.DoubleVar(value=default_durations[1])
        max_dur_slider = ttk.Scale(
            max_dur_frame,
            from_=1.0,
            to=5.0,
            orient="horizontal",
            variable=self.edit_max_dur_var
        )
        max_dur_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        max_dur_label = ttk.Label(
            max_dur_frame, 
            textvariable=self.edit_max_dur_var,
            width=5
        )
        max_dur_label.pack(side="left")

    def setup_settings_tab(self, parent):
        """Set up the settings tab with application preferences"""
        # Create a scrollable container
        settings_canvas = tk.Canvas(parent, highlightthickness=0, bg=self.colors["bg_primary"])
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=settings_canvas.yview)
        
        settings_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        settings_canvas.pack(side="left", fill="both", expand=True)
        
        content_frame = ttk.Frame(settings_canvas, style='TFrame')
        content_window = settings_canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        def configure_settings_canvas(event):
            settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
            settings_canvas.itemconfig(content_window, width=event.width)
            
        settings_canvas.bind("<Configure>", configure_settings_canvas)
        content_frame.bind("<Configure>", lambda e: settings_canvas.configure(scrollregion=settings_canvas.bbox("all")))
        
        # General Settings card
        general_card = self.create_card(content_frame, "General Settings")
        general_card.pack(fill="x", pady=(0, 10))
        
        # Default profile
        default_frame = ttk.Frame(general_card, style='Card.TFrame')
        default_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            default_frame, 
            text="Default Profile:",
            style='Card.TLabel'
        ).pack(side="left")
        
        self.default_profile_var = tk.StringVar(value=self.settings["default_profile"])
        default_combo = ttk.Combobox(
            default_frame,
            textvariable=self.default_profile_var,
            values=list(self.typing_profiles.keys()),
            width=15,
            state="readonly"
        )
        default_combo.pack(side="left", padx=5)
        
        # Startup behavior section
        startup_frame = ttk.Frame(general_card, style='Card.TFrame')
        startup_frame.pack(fill="x", pady=5)
        
        # Start minimized
        self.startup_min_var = tk.BooleanVar(value=self.settings["startup_minimized"])
        startup_min_cb = ttk.Checkbutton(
            startup_frame,
            text="Start Minimized to System Tray",
            variable=self.startup_min_var,
            style='Card.TCheckbutton'
        )
        startup_min_cb.pack(anchor="w", pady=2)
        
        # Always on top
        self.settings_aot_var = tk.BooleanVar(value=self.settings["always_on_top"])
        settings_aot_cb = ttk.Checkbutton(
            startup_frame,
            text="Always on Top",
            variable=self.settings_aot_var,
            style='Card.TCheckbutton'
        )
        settings_aot_cb.pack(anchor="w", pady=2)
        
        # Sound settings
        self.settings_sound_var = tk.BooleanVar(value=self.settings["sound_enabled"])
        settings_sound_cb = ttk.Checkbutton(
            startup_frame,
            text="Enable Sound Effects",
            variable=self.settings_sound_var,
            style='Card.TCheckbutton'
        )
        settings_sound_cb.pack(anchor="w", pady=2)
        
        # Sound volume
        sound_vol_frame = ttk.Frame(general_card, style='Card.TFrame')
        sound_vol_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            sound_vol_frame, 
            text="Sound Volume:",
            style='Card.TLabel'
        ).pack(side="left")
        
        self.sound_vol_var = tk.DoubleVar(value=self.settings["sound_volume"])
        sound_vol_slider = ttk.Scale(
            sound_vol_frame,
            from_=0.0,
            to=1.0,
            orient="horizontal",
            variable=self.sound_vol_var
        )
        sound_vol_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        # Format volume as percentage
        sound_vol_formatted = tk.StringVar(value=f"{self.sound_vol_var.get()*100:.0f}%")
        
        def update_sound_vol(*args):
            sound_vol_formatted.set(f"{self.sound_vol_var.get()*100:.0f}%")
            
        self.sound_vol_var.trace_add("write", update_sound_vol)
        
        sound_vol_label = ttk.Label(
            sound_vol_frame, 
            textvariable=sound_vol_formatted,
            style='Card.TLabel',
            width=5
        )
        sound_vol_label.pack(side="left")
        
        # Smooth typing
        self.smooth_typing_var = tk.BooleanVar(value=self.settings["smooth_typing"])
        smooth_typing_cb = ttk.Checkbutton(
            startup_frame,
            text="Smooth Typing Animation",
            variable=self.smooth_typing_var,
            style='Card.TCheckbutton'
        )
        smooth_typing_cb.pack(anchor="w", pady=2)
        
        # Mini panel
        self.settings_mini_panel_var = tk.BooleanVar(value=self.settings["mini_panel_enabled"])
        settings_mini_panel_cb = ttk.Checkbutton(
            startup_frame,
            text="Enable Mini Control Panel",
            variable=self.settings_mini_panel_var,
            style='Card.TCheckbutton'
        )
        settings_mini_panel_cb.pack(anchor="w", pady=2)
        
        # Clipboard monitoring
        self.clipboard_monitoring_var = tk.BooleanVar(value=self.settings["clipboard_monitoring"])
        clipboard_monitoring_cb = ttk.Checkbutton(
            startup_frame,
            text="Monitor Clipboard for Text",
            variable=self.clipboard_monitoring_var,
            style='Card.TCheckbutton'
        )
        clipboard_monitoring_cb.pack(anchor="w", pady=2)
        
        # Hotkeys card
        hotkeys_card = self.create_card(content_frame, "Keyboard Shortcuts")
        hotkeys_card.pack(fill="x", pady=10)
        
        # Add instruction
        instruction_label = ttk.Label(
            hotkeys_card,
            text="Click on a shortcut to change it. Press your desired key combination when prompted.",
            style='Card.TLabel',
            wraplength=500
        )
        instruction_label.pack(anchor="w", pady=(0, 10))
        
        # Create hotkey buttons
        self.hotkey_vars = {}
        
        hotkey_grid = ttk.Frame(hotkeys_card, style='Card.TFrame')
        hotkey_grid.pack(fill="x")
        
        # Configure grid columns
        hotkey_grid.columnconfigure(0, weight=2)
        hotkey_grid.columnconfigure(1, weight=3)
        
        # Add each hotkey with a button
        for i, (action, hotkey) in enumerate(self.settings["hotkeys"].items()):
            # Format the action name
            action_display = " ".join(word.capitalize() for word in action.split("_"))
            
            # Create label
            ttk.Label(
                hotkey_grid,
                text=f"{action_display}:",
                style='Card.TLabel'
            ).grid(row=i, column=0, sticky="w", pady=5)
            
            # Create variable for hotkey
            self.hotkey_vars[action] = tk.StringVar(value=hotkey)
            
            # Create button to edit
            hotkey_btn = ttk.Button(
                hotkey_grid,
                textvariable=self.hotkey_vars[action],
                width=20,
                command=lambda a=action: self.capture_hotkey(a)
            )
            hotkey_btn.grid(row=i, column=1, sticky="w", padx=10, pady=5)
        
        # Reset hotkeys button
        reset_btn = ttk.Button(
            hotkeys_card,
            text="Reset to Defaults",
            command=self.reset_hotkeys
        )
        reset_btn.pack(anchor="e", pady=(10, 0))
        
        # Appearance card
        appearance_card = self.create_card(content_frame, "Appearance")
        appearance_card.pack(fill="x", pady=10)
        
        # Theme selection
        theme_frame = ttk.Frame(appearance_card, style='Card.TFrame')
        theme_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            theme_frame, 
            text="Theme:",
            style='Card.TLabel'
        ).pack(side="left")
        
        self.settings_theme_var = tk.StringVar(value=self.theme_mode)
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.settings_theme_var,
            values=["light", "dark", "amoled"],
            width=10,
            state="readonly"
        )
        theme_combo.pack(side="left", padx=5)
        
        # UI scaling (if supported)
        if hasattr(tk, "ScalingValid"):  # Check if scaling is supported
            scaling_frame = ttk.Frame(appearance_card, style='Card.TFrame')
            scaling_frame.pack(fill="x", pady=5)
            
            ttk.Label(
                scaling_frame, 
                text="UI Scaling:",
                style='Card.TLabel'
            ).pack(side="left")
            
            current_scaling = self.root.tk.call('tk', 'scaling')
            self.scaling_var = tk.DoubleVar(value=current_scaling)
            
            scaling_slider = ttk.Scale(
                scaling_frame,
                from_=0.8,
                to=2.0,
                orient="horizontal",
                variable=self.scaling_var,
                command=self.update_ui_scaling
            )
            scaling_slider.pack(side="left", fill="x", expand=True, padx=5)
            
            scaling_label = ttk.Label(
                scaling_frame, 
                textvariable=self.scaling_var,
                style='Card.TLabel',
                width=4
            )
            scaling_label.pack(side="left")
            
            ttk.Button(
                scaling_frame,
                text="Reset",
                command=lambda: self.scaling_var.set(1.0)
            ).pack(side="left", padx=5)
        
        # Save and reset buttons
        button_frame = ttk.Frame(content_frame, style='TFrame')
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(
            button_frame,
            text="Save Settings",
            style='Accent.TButton',
            command=self.save_settings_from_ui
        ).pack(side="right")
        
        ttk.Button(
            button_frame,
            text="Reset All Settings",
            command=self.reset_all_settings
        ).pack(side="right", padx=5)

    def setup_about_tab(self, parent):
        """Set up the about tab with app information"""
        # Main container
        about_frame = ttk.Frame(parent, style='TFrame')
        about_frame.pack(fill="both", expand=True)
        
        # App info card
        info_card = self.create_card(about_frame, "About Enhanced Stealth Auto-Typer")
        info_card.pack(fill="x", pady=(0, 10))
        
        # App logo
        if HAS_PIL:
            try:
                # Create a larger logo for the about page
                logo_size = 100
                logo_img = Image.new('RGBA', (logo_size, logo_size), (0, 0, 0, 0))
                logo_draw = ImageDraw.Draw(logo_img)
                
                # Draw keyboard-like icon with accent color
                accent_color_rgb = self.hex_to_rgb(self.colors["accent_primary"])
                bg_color_rgb = self.hex_to_rgb(self.colors["card_bg"])
                
                # Draw background circle
                logo_draw.ellipse((0, 0, logo_size, logo_size), fill=bg_color_rgb)
                
                # Draw keyboard outline
                padding = 15
                logo_draw.rectangle(
                    (padding, padding+5, logo_size-padding, logo_size-padding-5), 
                    outline=accent_color_rgb, 
                    width=4
                )
                
                # Draw keys
                key_y = logo_size//2
                key_spacing = (logo_size-2*padding) // 6
                for i in range(6):
                    x = padding + i*key_spacing + key_spacing//2
                    logo_draw.rectangle((x-4, key_y-4, x+4, key_y+4), fill=accent_color_rgb)
                
                # Convert to PhotoImage
                about_logo_tk = ImageTk.PhotoImage(logo_img)
                
                # Display logo
                logo_label = ttk.Label(info_card, image=about_logo_tk, style='Card.TLabel')
                logo_label.image = about_logo_tk  # Keep a reference
                logo_label.pack(pady=10)
            except:
                pass
        
        # App name and version
        title_label = ttk.Label(
            info_card, 
            text="Enhanced Stealth Auto-Typer",
            style='Card.TLabel',
            font=('', 20, 'bold')
        )
        title_label.pack(pady=(0, 5))
        
        version_label = ttk.Label(
            info_card, 
            text=f"Version {self.version}",
            style='Card.TLabel',
            font=self.fonts["subheading"]
        )
        version_label.pack()
        
        # Description
        desc_text = (
            "A professional auto-typing tool with advanced human-like typing simulation.\n"
            "Perfect for demonstrations, testing, and automated typing tasks."
        )
        
        description = ttk.Label(
            info_card, 
            text=desc_text,
            style='Card.TLabel',
            wraplength=500,
            justify="center"
        )
        description.pack(pady=10)
        
        # Create a separator
        ttk.Separator(info_card, orient="horizontal").pack(fill="x", padx=50, pady=10)
        
        # Features section
        features_label = ttk.Label(
            info_card, 
            text="Key Features",
            style='Card.TLabel',
            font=self.fonts["subheading"]
        )
        features_label.pack(pady=(0, 5))
        
        # Feature list
        features = [
            "✓ Human-like typing with natural rhythm and pauses",
            "✓ Works with any application, even when not in focus",
            "✓ Customizable typing profiles for different scenarios",
            "✓ Global hotkeys for easy control",
            "✓ Advanced stealth options to avoid detection",
            "✓ Multiple typing modes for different situations"
        ]
        
        for feature in features:
            feature_label = ttk.Label(
                info_card, 
                text=feature,
                style='Card.TLabel'
            )
            feature_label.pack(anchor="w", padx=50, pady=1)
        
        # Credits card
        credits_card = self.create_card(about_frame, "Credits & Technical Info")
        credits_card.pack(fill="x", pady=10)
        
        # System info
        sys_info_text = (
            f"System: {platform.system()} {platform.release()}\n"
            f"Python: {platform.python_version()}\n"
            f"Tkinter: {tk.TkVersion}\n"
        )
        
        # Add additional module info
        if HAS_PIL:
            try:
                from PIL import __version__ as pil_version
                sys_info_text += f"PIL/Pillow: {pil_version}\n"
            except:
                sys_info_text += "PIL/Pillow: Installed\n"
        else:
            sys_info_text += "PIL/Pillow: Not installed\n"
        
        if HAS_SOUND:
            try:
                sys_info_text += f"Pygame: {pygame.version.ver}\n"
            except:
                sys_info_text += "Pygame: Installed\n"
        else:
            sys_info_text += "Pygame: Not installed\n"
        
        sys_info = ttk.Label(
            credits_card, 
            text=sys_info_text,
            style='Card.TLabel',
            justify="left"
        )
        sys_info.pack(anchor="w", padx=20, pady=10)
        
        # Legal and credits
        legal_text = (
            "This software is provided as-is without warranty of any kind.\n"
            "Use responsibly and ethically."
        )
        
        legal_label = ttk.Label(
            credits_card, 
            text=legal_text,
            style='Card.TLabel',
            wraplength=500,
            justify="center",
            foreground=self.colors["fg_secondary"]
        )
        legal_label.pack(pady=10)

    def create_card(self, parent, title=None):
        """Create a card-like container with title"""
        # Container frame with padding
        card = ttk.Frame(parent, style='Card.TFrame', padding=15)
        
        # Add title if provided
        if title:
            title_label = ttk.Label(
                card, 
                text=title,
                style='Card.TLabel',
                font=self.fonts["subheading"]
            )
            title_label.pack(anchor="w", pady=(0, 5))
            
            # Add separator
            ttk.Separator(card, orient="horizontal").pack(fill="x", pady=(0, 10))
        
        return card

    def create_status_bar(self, parent):
        """Create application status bar"""
        # Status bar frame with subtle separator
        status_frame = ttk.Frame(parent, style='Secondary.TFrame', padding=2)
        status_frame.pack(side="bottom", fill="x")
        
        # Add top separator
        ttk.Separator(parent, orient="horizontal").pack(side="bottom", fill="x")
        
        # Status message (left side)
        self.status_text = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_text,
            style='Secondary.TLabel',
            font=self.fonts["small"]
        )
        status_label.pack(side="left", padx=5)
        
        # App version (right side)
        version_label = ttk.Label(
            status_frame, 
            text=f"v{self.version}",
            style='Secondary.TLabel',
            font=self.fonts["tiny"]
        )
        version_label.pack(side="right", padx=5)
        
        # Hotkey hint
        hotkey_label = ttk.Label(
            status_frame, 
            text=f"Press {self.settings['hotkeys']['show_app']} to show app",
            style='Secondary.TLabel',
            font=self.fonts["small"]
        )
        hotkey_label.pack(side="right", padx=5)

    def apply_ui_effects(self):
        """Apply special UI effects and styling"""
        # Apply smooth corners to text widgets if PIL is available
        if HAS_PIL:
            try:
                # Custom styling for text widgets
                self.text_input.configure(insertwidth=2)
                
                # Update color scheme for related widgets
                self.preview_text.configure(
                    bg=self.colors["bg_input"],
                    fg=self.colors["fg_primary"],
                    insertbackground=self.colors["fg_primary"]
                )
            except:
                pass
        
        # Apply platform-specific tweaks
        if platform.system() == 'Windows':
            try:
                # Modern Windows look
                self.root.iconbitmap(default="NONE")
            except:
                pass
        
        # Update profile description
        if hasattr(self, 'profile_desc_var'):
            self.profile_desc_var.set(
                self.typing_profiles[self.current_profile]["description"]
            )

    def create_mini_panel(self):
        """Create a mini floating control panel"""
        if not self.settings["mini_panel_enabled"] or self.mini_panel:
            return
            
        # Create a new toplevel window
        self.mini_panel = tk.Toplevel(self.root)
        self.mini_panel.title("Typer Controls")
        self.mini_panel.geometry("320x60")
        self.mini_panel.resizable(False, False)
        
        # No window decorations for a cleaner look
        self.mini_panel.overrideredirect(True)
        
        # Set always on top
        self.mini_panel.attributes("-topmost", True)
        
        # Semi-transparent background for stealth
        if platform.system() == 'Windows':
            self.mini_panel.attributes("-alpha", 0.85)
        
        # Configure panel style based on theme
        self.mini_panel.configure(bg=self.colors["bg_primary"])
        
        # Add a border
        mini_frame = ttk.Frame(
            self.mini_panel, 
            style='Card.TFrame', 
            padding=5
        )
        mini_frame.pack(fill="both", expand=True)
        
        # Control buttons in a row
        btn_frame = ttk.Frame(mini_frame, style='Card.TFrame')
        btn_frame.pack(fill="x")
        
        # Start button
        start_btn = ttk.Button(
            btn_frame,
            text="Start",
            style='Success.TButton',
            width=8,
            command=self.start_typing
        )
        start_btn.pack(side="left", padx=2)
        
        # Pause button
        pause_btn = ttk.Button(
            btn_frame,
            text="Pause",
            width=8,
            command=self.toggle_pause
        )
        pause_btn.pack(side="left", padx=2)
        
        # Stop button
        stop_btn = ttk.Button(
            btn_frame,
            text="Stop",
            style='Error.TButton',
            width=8,
            command=self.stop_typing
        )
        stop_btn.pack(side="left", padx=2)
        
        # Show main app button
        show_btn = ttk.Button(
            btn_frame,
            text="≡",
            width=3,
            command=self.show_app
        )
        show_btn.pack(side="right", padx=(10, 0))
        
        # Close button
        close_btn = ttk.Button(
            btn_frame,
            text="×",
            width=3,
            command=self.close_mini_panel
        )
        close_btn.pack(side="right", padx=2)
        
        # Make window draggable
        def start_drag(event):
            self.mini_panel.x = event.x
            self.mini_panel.y = event.y
            
        def on_drag(event):
            deltax = event.x - self.mini_panel.x
            deltay = event.y - self.mini_panel.y
            x = self.mini_panel.winfo_x() + deltax
            y = self.mini_panel.winfo_y() + deltay
            self.mini_panel.geometry(f"+{x}+{y}")
            
        mini_frame.bind("<ButtonPress-1>", start_drag)
        mini_frame.bind("<B1-Motion>", on_drag)
        
        # Position the panel in the bottom right of the screen
        self.position_mini_panel()
        
        # Update when main window closes
        self.mini_panel.protocol("WM_DELETE_WINDOW", self.close_mini_panel)
        
        # Hide by default if main window is showing
        if not self.settings["startup_minimized"]:
            self.mini_panel.withdraw()

    def position_mini_panel(self):
        """Position the mini panel in a good spot on the screen"""
        if not self.mini_panel:
            return
            
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Panel size
        panel_width = 320
        panel_height = 60
        
        # Bottom right position
        x = screen_width - panel_width - 20
        y = screen_height - panel_height - 80
        
        self.mini_panel.geometry(f"{panel_width}x{panel_height}+{x}+{y}")

    def close_mini_panel(self):
        """Close the mini control panel"""
        if self.mini_panel:
            self.mini_panel.destroy()
            self.mini_panel = None

    def toggle_mini_panel(self):
        """Toggle the mini control panel on/off"""
        self.settings["mini_panel_enabled"] = self.mini_panel_var.get()
        
        if self.settings["mini_panel_enabled"]:
            if not self.mini_panel:
                self.create_mini_panel()
                self.mini_panel.deiconify()
        else:
            self.close_mini_panel()
        
        self.save_settings()

    def apply_platform_specifics(self):
        """Apply platform-specific customizations"""
        # Windows-specific tweaks
        if platform.system() == 'Windows':
            try:
                # Set taskbar icon
                if HAS_WIN32:
                    import ctypes
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.enhancedstealthtyper.app")
            except:
                pass
        
        # macOS-specific tweaks
        elif platform.system() == 'Darwin':
            try:
                # Set macOS menu bar
                self.root.createcommand('tk::mac::ReopenApplication', self.show_app)
            except:
                pass

    def update_wpm_display(self, event=None):
        """Update the WPM display label"""
        self.wpm_label.config(text=f"{self.wpm_var.get()} WPM")
        self.active_profile["base_wpm"] = self.wpm_var.get()

    def update_variation_display(self, event=None):
        """Update the variation display label"""
        self.variation_label.config(text=f"±{self.variation_var.get()}%")
        self.active_profile["wpm_variation"] = self.variation_var.get()

    def update_error_display(self, event=None):
        """Update the error rate display label"""
        self.error_label.config(text=f"{self.error_rate_var.get():.1f}%")
        self.active_profile["error_rate"] = self.error_rate_var.get()

    def update_profile(self, event=None):
        """Update current profile when selection changes"""
        self.current_profile = self.profile_var.get()
        if self.current_profile in self.typing_profiles:
            # Update profile description
            self.profile_desc_var.set(
                self.typing_profiles[self.current_profile]["description"]
            )

    def update_font_size(self, event=None):
        """Update font size for text input"""
        font_size = self.font_size_var.get()
        self.text_input.configure(font=(self.fonts["mono"][0], font_size))

    def update_ui_scaling(self, event=None):
        """Update UI scaling factor if supported"""
        if hasattr(tk, "ScalingValid"):
            scale_factor = self.scaling_var.get()
            self.root.tk.call('tk', 'scaling', scale_factor)

    def paste_from_clipboard(self):
        """Paste text from clipboard into text input"""
        try:
            clipboard_text = self.root.clipboard_get()
            if clipboard_text:
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", clipboard_text)
        except:
            messagebox.showwarning("Clipboard", "Failed to get text from clipboard.")

    def apply_profile(self):
        """Apply the selected profile settings"""
        self.active_profile = self.typing_profiles[self.current_profile].copy()
        
        # Update UI to match profile
        self.wpm_var.set(self.active_profile["base_wpm"])
        self.variation_var.set(self.active_profile["wpm_variation"])
        self.error_rate_var.set(self.active_profile["error_rate"])
        self.smart_pauses_var.set(self.active_profile["smart_pauses"])
        self.word_burst_var.set(self.active_profile["word_burst"])
        self.rhythm_var.set(self.active_profile["typing_rhythm"])
        
        # Set thought pause option if available
        has_thought_pauses = "thought_pause_probability" in self.active_profile
        self.thought_pause_var.set(has_thought_pauses and self.active_profile["thought_pause_probability"] > 0)
        
        # Update display labels
        self.update_wpm_display()
        self.update_variation_display()
        self.update_error_display()
        
        # Show success message in status bar
        self.status_text.set(f"Applied '{self.current_profile}' profile")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def toggle_always_on_top(self):
        """Toggle always on top setting"""
        self.settings["always_on_top"] = self.always_on_top_var.get()
        self.root.attributes("-topmost", self.always_on_top_var.get())
        self.save_settings()

    def toggle_sound(self):
        """Toggle sound effects"""
        self.sound_enabled = self.sound_var.get()
        self.settings["sound_enabled"] = self.sound_enabled
        self.save_settings()

    def change_theme(self, event=None):
        """Change the application theme"""
        self.theme_mode = self.theme_var.get()
        self.settings["theme"] = self.theme_mode
        
        # Update colors
        self.init_colors()
        
        # Recreate styles
        self.setup_styles()
        
        # Update existing widgets with new colors
        self.update_widget_colors()
        
        self.save_settings()
        
        # Show success message
        self.status_text.set(f"Changed theme to {self.theme_mode}")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def update_widget_colors(self):
        """Update colors of existing widgets after theme change"""
        # Update text input colors
        self.text_input.configure(
            bg=self.colors["bg_input"],
            fg=self.colors["fg_primary"],
            insertbackground=self.colors["fg_primary"]
        )
        
        # Update preview text
        self.preview_text.configure(
            bg=self.colors["bg_input"],
            fg=self.colors["fg_primary"],
            insertbackground=self.colors["fg_primary"]
        )
        
        # Update tags
        self.preview_text.tag_configure("cursor", background=self.colors["accent_primary"])
        self.preview_text.tag_configure("typed", foreground=self.colors["accent_secondary"])
        self.preview_text.tag_configure("untyped", foreground=self.colors["fg_secondary"])
        
        # Update status indicator color
        if hasattr(self, 'status_indicator'):
            self.status_indicator.configure(bg=self.colors["card_bg"])
            
        # Update mini panel if exists
        if self.mini_panel:
            self.mini_panel.configure(bg=self.colors["bg_primary"])

    def load_from_file(self):
        """Load text from a file"""
        file_path = filedialog.askopenfilename(
            initialdir=self.settings["last_directory"],
            title="Select a Text File",
            filetypes=(
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("HTML files", "*.html"),
                ("All files", "*.*")
            )
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.text_input.delete("1.0", tk.END)
                    self.text_input.insert("1.0", f.read())
                self.settings["last_directory"] = os.path.dirname(file_path)
                self.save_settings()
                
                # Show success message
                filename = os.path.basename(file_path)
                self.status_text.set(f"Loaded {filename}")
                
                # Clear status after a delay
                self.root.after(3000, lambda: self.status_text.set("Ready"))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def save_to_file(self):
        """Save text to a file"""
        file_path = filedialog.asksaveasfilename(
            initialdir=self.settings["last_directory"],
            title="Save Text",
            filetypes=(
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ),
            defaultextension=".txt"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_input.get("1.0", tk.END))
                self.settings["last_directory"] = os.path.dirname(file_path)
                self.save_settings()
                
                # Show success message
                filename = os.path.basename(file_path)
                self.status_text.set(f"Saved to {filename}")
                
                # Clear status after a delay
                self.root.after(3000, lambda: self.status_text.set("Ready"))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def capture_hotkey(self, action):
        """Capture a new hotkey combination"""
        # Create a dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Capture Hotkey")
        dialog.geometry("300x150")
        dialog.configure(bg=self.colors["bg_primary"])
        dialog.resizable(False, False)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center on parent
        x = self.root.winfo_x() + (self.root.winfo_width() / 2) - (300 / 2)
        y = self.root.winfo_y() + (self.root.winfo_height() / 2) - (150 / 2)
        dialog.geometry(f"+{int(x)}+{int(y)}")
        
        # Instruction label
        instruction = ttk.Label(
            dialog,
            text="Press your desired key combination...",
            font=self.fonts["subheading"],
            style='TLabel'
        )
        instruction.pack(pady=(20, 10))
        
        # Key display
        key_var = tk.StringVar(value="Listening for keypress...")
        key_label = ttk.Label(
            dialog,
            textvariable=key_var,
            font=self.fonts["mono_bold"],
            style='TLabel'
        )
        key_label.pack(pady=10)
        
        # Button to cancel
        ttk.Button(
            dialog,
            text="Cancel",
            command=dialog.destroy
        ).pack(pady=10)
        
        def on_key_press(e):
            # Format key combination
            hotkey = "+".join(sorted([k for k in ['ctrl', 'alt', 'shift'] if keyboard.is_pressed(k)]))
            
            # Add the main key
            main_key = e.name
            if main_key not in ['ctrl', 'alt', 'shift']:
                if hotkey:
                    hotkey += f"+{main_key}"
                else:
                    hotkey = main_key
                    
            # Update dialog
            key_var.set(hotkey)
            
            # Update the hotkey variable
            self.hotkey_vars[action].set(hotkey)
            
            # Close dialog after a short delay
            dialog.after(500, dialog.destroy)
        
        # Hook keyboard
        hook_id = keyboard.on_press(on_key_press)
        
        # Clean up when dialog closes
        def on_dialog_close():
            keyboard.unhook(hook_id)
            dialog.destroy()
            
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        
        # Wait for dialog to close
        self.root.wait_window(dialog)

    def reset_hotkeys(self):
        """Reset hotkeys to defaults"""
        default_hotkeys = {
            "start_typing": "ctrl+shift+f9",
            "pause_typing": "ctrl+shift+f10",
            "stop_typing": "ctrl+shift+f11",
            "show_app": "ctrl+shift+f12",
            "mini_panel": "ctrl+shift+space"
        }
        
        # Update UI variables
        for action, hotkey in default_hotkeys.items():
            if action in self.hotkey_vars:
                self.hotkey_vars[action].set(hotkey)
        
        # Show confirmation message
        self.status_text.set("Reset hotkeys to defaults")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def save_settings_from_ui(self):
        """Save settings from UI values"""
        # General settings
        self.settings["default_profile"] = self.default_profile_var.get()
        self.settings["startup_minimized"] = self.startup_min_var.get()
        self.settings["always_on_top"] = self.settings_aot_var.get()
        self.settings["sound_enabled"] = self.settings_sound_var.get()
        self.settings["sound_volume"] = self.sound_vol_var.get()
        self.settings["mini_panel_enabled"] = self.settings_mini_panel_var.get()
        self.settings["clipboard_monitoring"] = self.clipboard_monitoring_var.get()
        self.settings["theme"] = self.settings_theme_var.get()
        self.settings["smooth_typing"] = self.smooth_typing_var.get()
        
        # Hotkeys
        for action, var in self.hotkey_vars.items():
            self.settings["hotkeys"][action] = var.get()
        
        # Apply changes
        self.theme_mode = self.settings["theme"]
        self.sound_enabled = self.settings["sound_enabled"]
        
        # Apply always on top
        self.root.attributes("-topmost", self.settings["always_on_top"])
        self.always_on_top_var.set(self.settings["always_on_top"])
        
        # Update mini panel
        if self.settings["mini_panel_enabled"] and not self.mini_panel:
            self.create_mini_panel()
        elif not self.settings["mini_panel_enabled"] and self.mini_panel:
            self.close_mini_panel()
        
        # Update theme if changed
        if self.theme_mode != self.theme_var.get():
            self.theme_var.set(self.theme_mode)
            self.change_theme()
        
        # Save to file
        self.save_settings()
        
        # Re-register hotkeys
        self.register_hotkeys()
        
        # Show success message
        self.status_text.set("Settings saved successfully")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def reset_all_settings(self):
        """Reset all settings to defaults"""
        # Ask for confirmation
        confirm = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?"
        )
        
        if not confirm:
            return
            
        # Default settings
        default_settings = {
            "default_profile": "Natural",
            "hotkeys": {
                "start_typing": "ctrl+shift+f9",
                "pause_typing": "ctrl+shift+f10",
                "stop_typing": "ctrl+shift+f11",
                "show_app": "ctrl+shift+f12",
                "mini_panel": "ctrl+shift+space"
            },
            "startup_minimized": False,
            "always_on_top": False,
            "last_directory": os.path.expanduser("~"),
            "theme": "dark",
            "sound_enabled": True,
            "sound_volume": 0.3,
            "clipboard_monitoring": False,
            "mini_panel_enabled": True,
            "smooth_typing": True
        }
        
        # Update settings
        self.settings = default_settings.copy()
        
        # Apply to UI
        self.default_profile_var.set(self.settings["default_profile"])
        self.startup_min_var.set(self.settings["startup_minimized"])
        self.settings_aot_var.set(self.settings["always_on_top"])
        self.settings_sound_var.set(self.settings["sound_enabled"])
        self.sound_vol_var.set(self.settings["sound_volume"])
        self.settings_mini_panel_var.set(self.settings["mini_panel_enabled"])
        self.clipboard_monitoring_var.set(self.settings["clipboard_monitoring"])
        self.settings_theme_var.set(self.settings["theme"])
        self.smooth_typing_var.set(self.settings["smooth_typing"])
        
        # Update hotkey variables
        for action, hotkey in self.settings["hotkeys"].items():
            if action in self.hotkey_vars:
                self.hotkey_vars[action].set(hotkey)
        
        # Apply changes
        self.save_settings_from_ui()
        
        # Show success message
        self.status_text.set("All settings reset to defaults")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def on_profile_selected(self, event):
        """Handle profile selection in the profile list"""
        selection = self.profile_list.curselection()
        if not selection:
            return
            
        # Get selected profile name
        index = selection[0]
        profile_name = self.profile_list.get(index)
        
        # Set as current edit profile
        self.profile_edit_name_var.set(profile_name)
        self.profile_name_var.set(profile_name)
        
        # Load profile settings into UI
        self.load_profile_for_editing(profile_name)

    def load_profile_for_editing(self, profile_name):
        """Load profile settings into the profile editor UI"""
        if profile_name not in self.typing_profiles:
            return
            
        # Get profile
        profile = self.typing_profiles[profile_name]
        
        # Set basic settings
        self.profile_desc_edit_var.set(profile["description"])
        self.edit_wpm_var.set(profile["base_wpm"])
        self.edit_var_var.set(profile["wpm_variation"])
        self.edit_error_var.set(profile["error_rate"])
        self.edit_smart_pauses_var.set(profile["smart_pauses"])
        self.edit_word_burst_var.set(profile["word_burst"])
        self.edit_rhythm_var.set(profile["typing_rhythm"])
        
        # Sound profile
        if "sound_profile" in profile:
            self.edit_sound_var.set(profile["sound_profile"])
        else:
            self.edit_sound_var.set("standard")
        
        # Burst settings
        self.edit_burst_prob_var.set(profile["burst_probability"])
        self.edit_burst_speed_var.set(profile["burst_speed_multiplier"])
        
        # Thought pause settings (if available)
        self.edit_thought_enable_var.set("thought_pause_probability" in profile)
        self.edit_thought_prob_var.set(profile.get("thought_pause_probability", 0.08))
        
        # Get thought pause duration or set defaults
        thought_duration = profile.get("thought_pause_duration", (0.8, 3.0))
        self.edit_min_dur_var.set(thought_duration[0])
        self.edit_max_dur_var.set(thought_duration[1])
        
        # Set pause multipliers
        for char, multiplier in profile["pause_multiplier"].items():
            if char in self.multiplier_vars:
                self.multiplier_vars[char].set(multiplier)

    def save_profile_changes(self):
        """Save changes to the current profile"""
        # Get the profile name (original and potentially new)
        original_name = self.profile_edit_name_var.get()
        new_name = self.profile_name_var.get().strip()
        
        # Validate profile name
        if not new_name:
            messagebox.showerror("Error", "Profile name cannot be empty.")
            return
            
        # Check if name changed and already exists
        if original_name != new_name and new_name in self.typing_profiles:
            confirm = messagebox.askyesno(
                "Profile Exists",
                f"A profile named '{new_name}' already exists. Overwrite it?"
            )
            if not confirm:
                return
        
        # Create updated profile
        updated_profile = {}
        
        # Basic settings
        updated_profile["description"] = self.profile_desc_edit_var.get()
        updated_profile["base_wpm"] = self.edit_wpm_var.get()
        updated_profile["wpm_variation"] = self.edit_var_var.get()
        updated_profile["error_rate"] = self.edit_error_var.get()
        updated_profile["smart_pauses"] = self.edit_smart_pauses_var.get()
        updated_profile["word_burst"] = self.edit_word_burst_var.get()
        updated_profile["typing_rhythm"] = self.edit_rhythm_var.get()
        updated_profile["sound_profile"] = self.edit_sound_var.get()
        
        # Burst settings
        updated_profile["burst_probability"] = self.edit_burst_prob_var.get()
        updated_profile["burst_speed_multiplier"] = self.edit_burst_speed_var.get()
        
        # Thought pause settings
        if self.edit_thought_enable_var.get():
            updated_profile["thought_pause_probability"] = self.edit_thought_prob_var.get()
            updated_profile["thought_pause_duration"] = (
                self.edit_min_dur_var.get(),
                self.edit_max_dur_var.get()
            )
            
        # Pause multipliers
        updated_profile["pause_multiplier"] = {}
        for char, var in self.multiplier_vars.items():
            updated_profile["pause_multiplier"][char] = var.get()
            
        # Key press duration (keep original or set default)
        if original_name in self.typing_profiles:
            updated_profile["key_press_duration"] = self.typing_profiles[original_name].get(
                "key_press_duration", (0.01, 0.05)
            )
        else:
            updated_profile["key_press_duration"] = (0.01, 0.05)
            
        # If name changed, remove old profile
        if original_name != new_name and original_name in self.typing_profiles:
            del self.typing_profiles[original_name]
            
        # Save updated profile
        self.typing_profiles[new_name] = updated_profile
        
        # Update profile selection UI
        self.update_profile_ui()
        
        # If current profile was updated, apply changes
        if self.current_profile == original_name:
            self.current_profile = new_name
            self.profile_var.set(new_name)
            self.active_profile = self.typing_profiles[new_name].copy()
        
        # Update profile description
        if new_name == self.current_profile:
            self.profile_desc_var.set(updated_profile["description"])
            
        # Save profiles to file
        self.save_profiles_to_file()
        
        # Show success message
        self.status_text.set(f"Profile '{new_name}' saved")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def discard_profile_changes(self):
        """Discard changes to the current profile"""
        # Reload the current profile
        selection = self.profile_list.curselection()
        if selection:
            index = selection[0]
            profile_name = self.profile_list.get(index)
            self.load_profile_for_editing(profile_name)
            
            # Show message
            self.status_text.set("Changes discarded")
            
            # Clear status after a delay
            self.root.after(3000, lambda: self.status_text.set("Ready"))

    def create_new_profile(self):
        """Create a new typing profile"""
        # Find a unique name
        base_name = "New Profile"
        profile_name = base_name
        counter = 1
        
        while profile_name in self.typing_profiles:
            profile_name = f"{base_name} {counter}"
            counter += 1
            
        # Create a default profile
        self.typing_profiles[profile_name] = {
            "base_wpm": 60,
            "wpm_variation": 20,
            "error_rate": 2,
            "smart_pauses": True,
            "pause_multiplier": {
                ".": 3.0,
                ",": 2.0,
                ";": 2.0,
                ":": 2.0,
                "?": 3.0,
                "!": 3.0,
                "(": 1.5,
                ")": 1.5,
                "{": 2.0,
                "}": 2.0,
                "\n": 4.0,
                "\t": 2.0
            },
            "word_burst": True,
            "burst_probability": 0.4,
            "burst_speed_multiplier": 1.5,
            "typing_rhythm": "natural",
            "key_press_duration": (0.01, 0.05),
            "sound_profile": "standard",
            "description": "Custom typing profile"
        }
        
        # Update profile list
        self.update_profile_ui()
        
        # Select the new profile
        index = list(self.typing_profiles.keys()).index(profile_name)
        self.profile_list.selection_clear(0, tk.END)
        self.profile_list.selection_set(index)
        self.profile_list.see(index)
        
        # Load it for editing
        self.load_profile_for_editing(profile_name)
        self.profile_edit_name_var.set(profile_name)
        self.profile_name_var.set(profile_name)
        
        # Show success message
        self.status_text.set(f"Created new profile: {profile_name}")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def clone_profile(self):
        """Clone the currently selected profile"""
        # Get selected profile
        selection = self.profile_list.curselection()
        if not selection:
            messagebox.showwarning("Clone", "Please select a profile to clone.")
            return
            
        index = selection[0]
        source_name = self.profile_list.get(index)
        
        if source_name not in self.typing_profiles:
            return
            
        # Find a unique name for the clone
        base_name = f"{source_name} Copy"
        profile_name = base_name
        counter = 1
        
        while profile_name in self.typing_profiles:
            profile_name = f"{base_name} {counter}"
            counter += 1
            
        # Clone the profile
        self.typing_profiles[profile_name] = self.typing_profiles[source_name].copy()
        
        # Update description
        self.typing_profiles[profile_name]["description"] = f"Copy of {source_name}"
        
        # Update profile list
        self.update_profile_ui()
        
        # Select the new profile
        index = list(self.typing_profiles.keys()).index(profile_name)
        self.profile_list.selection_clear(0, tk.END)
        self.profile_list.selection_set(index)
        self.profile_list.see(index)
        
        # Load it for editing
        self.load_profile_for_editing(profile_name)
        self.profile_edit_name_var.set(profile_name)
        self.profile_name_var.set(profile_name)
        
        # Save to file
        self.save_profiles_to_file()
        
        # Show success message
        self.status_text.set(f"Cloned profile as: {profile_name}")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def delete_profile(self):
        """Delete the currently selected profile"""
        # Get selected profile
        selection = self.profile_list.curselection()
        if not selection:
            messagebox.showwarning("Delete", "Please select a profile to delete.")
            return
            
        index = selection[0]
        profile_name = self.profile_list.get(index)
        
        # Prevent deleting last profile
        if len(self.typing_profiles) <= 1:
            messagebox.showerror("Error", "Cannot delete the last profile.")
            return
            
        # Prevent deleting default built-in profiles
        if profile_name in ["Executive", "Programmer", "Natural", "Realistic Student", "Ultra Stealth"]:
            confirm = messagebox.askyesno(
                "Delete Built-in Profile",
                f"'{profile_name}' is a built-in profile. Are you sure you want to delete it?\n\nYou can restore it by resetting to defaults."
            )
            if not confirm:
                return
        else:
            # Ask for confirmation
            confirm = messagebox.askyesno(
                "Delete Profile",
                f"Are you sure you want to delete the profile '{profile_name}'?"
            )
            if not confirm:
                return
                
        # Delete the profile
        del self.typing_profiles[profile_name]
        
        # If current profile was deleted, switch to another one
        if self.current_profile == profile_name:
            self.current_profile = next(iter(self.typing_profiles))
            self.profile_var.set(self.current_profile)
            self.active_profile = self.typing_profiles[self.current_profile].copy()
            self.profile_desc_var.set(self.typing_profiles[self.current_profile]["description"])
            
        # If default profile was deleted, update it
        if self.settings["default_profile"] == profile_name:
            self.settings["default_profile"] = self.current_profile
            if hasattr(self, 'default_profile_var'):
                self.default_profile_var.set(self.current_profile)
            self.save_settings()
        
        # Update profile list
        self.update_profile_ui()
        
        # Select another profile
        if self.profile_list.size() > 0:
            self.profile_list.selection_set(0)
            self.load_profile_for_editing(self.profile_list.get(0))
            
        # Save to file
        self.save_profiles_to_file()
        
        # Show success message
        self.status_text.set(f"Deleted profile: {profile_name}")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def update_profile_ui(self):
        """Update profile-related UI elements"""
        # Update profile list
        self.profile_list.delete(0, tk.END)
        for profile in self.typing_profiles:
            self.profile_list.insert(tk.END, profile)
            
        # Update profile combobox values
        profiles = list(self.typing_profiles.keys())
        self.profile_combo['values'] = profiles
        
        if hasattr(self, 'default_profile_var'):
            default_combo = self.nametowidget(
                self.default_profile_var.get_master().winfo_parent()
            ).children['!combobox']
            default_combo['values'] = profiles

    def export_profiles(self):
        """Export typing profiles to a file"""
        file_path = filedialog.asksaveasfilename(
            initialdir=self.settings["last_directory"],
            title="Export Typing Profiles",
            filetypes=(
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ),
            defaultextension=".json"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.typing_profiles, f, indent=2)
                    
                # Update last directory
                self.settings["last_directory"] = os.path.dirname(file_path)
                self.save_settings()
                
                # Show success message
                self.status_text.set(f"Exported {len(self.typing_profiles)} profiles")
                
                # Clear status after a delay
                self.root.after(3000, lambda: self.status_text.set("Ready"))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export profiles: {str(e)}")

    def import_profiles(self):
        """Import typing profiles from a file"""
        file_path = filedialog.askopenfilename(
            initialdir=self.settings["last_directory"],
            title="Import Typing Profiles",
            filetypes=(
                ("JSON files", "*.json"),
                ("All files", "*.*")
            )
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_profiles = json.load(f)
                    
                # Validate imported data
                if not isinstance(imported_profiles, dict):
                    raise ValueError("Invalid profile format")
                    
                # Count profiles to import
                count = 0
                for name, profile in imported_profiles.items():
                    # Basic validation of required fields
                    if not all(k in profile for k in ["base_wpm", "pause_multiplier"]):
                        continue
                        
                    # Add profile
                    self.typing_profiles[name] = profile
                    count += 1
                    
                # Update profile UI
                self.update_profile_ui()
                
                # Save to file
                self.save_profiles_to_file()
                
                # Update last directory
                self.settings["last_directory"] = os.path.dirname(file_path)
                self.save_settings()
                
                # Show success message
                self.status_text.set(f"Imported {count} profiles")
                
                # Clear status after a delay
                self.root.after(3000, lambda: self.status_text.set("Ready"))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import profiles: {str(e)}")
    def register_hotkeys(self):
        """Register global hotkeys"""
        # Unregister existing hotkeys first
        keyboard.unhook_all()
    
        # Register new hotkeys
        try:
            keyboard.add_hotkey(self.settings["hotkeys"]["start_typing"], self.start_typing)
            keyboard.add_hotkey(self.settings["hotkeys"]["pause_typing"], self.toggle_pause)
            keyboard.add_hotkey(self.settings["hotkeys"]["stop_typing"], self.stop_typing)
            keyboard.add_hotkey(self.settings["hotkeys"]["show_app"], self.show_app)
            keyboard.add_hotkey(self.settings["hotkeys"]["mini_panel"], self.toggle_mini_panel_visibility)
        except Exception as e:
            print(f"Error registering hotkeys: {e}")
            messagebox.showerror("Hotkey Error", f"Failed to register hotkeys: {str(e)}")

    def toggle_mini_panel_visibility(self):
        """Toggle mini panel visibility"""
        if not self.mini_panel:
            self.create_mini_panel()
            self.mini_panel.deiconify()
        else:
            if self.mini_panel.state() == 'normal':
                self.mini_panel.withdraw()
            else:
                self.mini_panel.deiconify()
                self.mini_panel.attributes("-topmost", True)
                self.mini_panel.attributes("-topmost", False)
    
    def show_app(self):
        """Show the application window"""
        # Restore window
        self.root.deiconify()
        self.root.lift()
        
        # Apply always on top if needed
        if self.settings["always_on_top"]:
            self.root.attributes("-topmost", True)
            
        # Show success message
        self.status_text.set("Application restored")
        
        # Clear status after a delay
        self.root.after(3000, lambda: self.status_text.set("Ready"))

    def setup_system_tray(self):
        """Set up the system tray icon"""
        if not HAS_SYSTEM_TRAY:
            return
            
        # Create icon image
        icon_image = self.create_tray_icon()
        
        # Create menu
        menu = (
            pystray.MenuItem('Show App', self.on_tray_show),
            pystray.MenuItem('Toggle Mini Panel', self.on_tray_toggle_mini),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Start Typing', self.on_tray_start),
            pystray.MenuItem('Pause/Resume', self.on_tray_pause),
            pystray.MenuItem('Stop', self.on_tray_stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self.on_tray_exit)
        )
        
        # Create system tray icon
        self.system_tray_icon = pystray.Icon("stealth_typer", icon_image, "Stealth Auto-Typer", menu)
        
        # Start system tray in a separate thread
        threading.Thread(target=self.system_tray_icon.run, daemon=True).start()
        
        # Capture window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_tray_icon(self):
        """Create an icon for the system tray"""
        icon_size = 64
        image = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw circle background
        bg_color = self.hex_to_rgb(self.colors["accent_primary"])
        draw.ellipse((4, 4, icon_size-4, icon_size-4), fill=bg_color)
        
        # Draw keyboard-like symbol
        draw.rectangle((16, 24, 48, 40), fill="white")
        
        # Draw some keys
        key_positions = [(20, 28), (28, 28), (36, 28), (44, 28)]
        for x, y in key_positions:
            draw.rectangle((x-3, y-3, x+3, y+3), fill=bg_color)
            
        return image
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def on_tray_show(self, icon, item):
        """Show the main window from system tray"""
        self.root.after(0, self.show_app)
        
    def on_tray_toggle_mini(self, icon, item):
        """Toggle mini panel from system tray"""
        self.root.after(0, self.toggle_mini_panel_visibility)
        
    def on_tray_start(self, icon, item):
        """Start typing from system tray"""
        self.root.after(0, self.start_typing)
        
    def on_tray_pause(self, icon, item):
        """Toggle pause from system tray"""
        self.root.after(0, self.toggle_pause)
        
    def on_tray_stop(self, icon, item):
        """Stop typing from system tray"""
        self.root.after(0, self.stop_typing)
        
    def on_tray_exit(self, icon, item):
        """Exit the application from system tray"""
        icon.stop()
        self.root.after(100, self.root.destroy)
        
    def on_close(self):
        """Handle window close event"""
        # Hide the window instead of closing
        self.root.withdraw()
        
        # If system tray is not available, destroy the application
        if not HAS_SYSTEM_TRAY:
            self.root.destroy()
            return
            
        # Show notification
        if self.system_tray_icon:
            self.system_tray_icon.notify(
                "Stealth Auto-Typer is still running in the background.\n"
                "Click the tray icon to restore."
            )

    def start_typing(self):
        """Start the typing process"""
        # Get text to type
        text_to_type = self.text_input.get("1.0", "end-1c")
        if not text_to_type:
            messagebox.showwarning("No Text", "Please enter text to type.")
            return
            
        # Check if we're already typing
        if self.is_typing and not self.is_paused:
            return
            
        # If paused, just resume
        if self.is_typing and self.is_paused:
            self.toggle_pause()
            return
            
        # Set typing state
        self.is_typing = True
        self.is_paused = False
        
        # Update UI
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        self.status_var.set("Preparing...")
        
        # Update status indicator
        self.update_status_indicator("typing")
        
        # Reset progress
        self.chars_typed = 0
        self.total_chars = len(text_to_type)
        self.progress_var.set(0)
        self.progress_label.config(text=f"0/{self.total_chars} chars")
        self.current_wpm_var.set("0 WPM")
        
        # Update status bar
        self.status_text.set("Typing in progress")
        
        # Start typing thread
        self.typing_thread = threading.Thread(
            target=self.type_text,
            args=(text_to_type,),
            daemon=True
        )
        self.typing_thread.start()
    
    def toggle_pause(self):
        """Toggle pause state"""
        if not self.is_typing:
            return
            
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_btn.config(text="Resume")
            self.status_var.set("Paused")
            self.update_status_indicator("paused")
            self.status_text.set("Typing paused")
        else:
            self.pause_btn.config(text="Pause")
            self.status_var.set("Typing...")
            self.update_status_indicator("typing")
            self.status_text.set("Typing resumed")
    
    def stop_typing(self):
        """Stop the typing process"""
        if not self.is_typing:
            return
            
        self.is_typing = False
        
        # Update UI
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.status_var.set("Stopped")
        self.pause_btn.config(text="Pause")
        
        # Update status indicator
        self.update_status_indicator("stopped")
        
        # Reset preview
        self.update_preview("", 0)
        
        # Update status bar
        self.status_text.set("Typing stopped")
    
    def update_status_indicator(self, status):
        """Update the status indicator circle color"""
        if status == "typing":
            color = self.colors["success"]
        elif status == "paused":
            color = self.colors["warning"]
        elif status == "stopped":
            color = self.colors["error"]
        else:
            color = self.colors["fg_tertiary"]
            
        self.status_indicator.itemconfig(self.status_circle, fill=color)

    def update_preview(self, text, index):
        """Update the character preview with formatting"""
        if not text:
            # Display empty preview
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", "No text to type")
            self.preview_text.config(state="disabled")
            return
            
        # Determine boundaries for preview (show ~50 chars around current position)
        start = max(0, index - 20)
        end = min(len(text), index + 30)
        
        preview = text[start:end]
        
        # Add ellipsis if needed
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        
        # Calculate cursor position
        cursor_pos = index - start
        if prefix:
            cursor_pos += 3
            
        # Prepare display text
        display_text = prefix + preview + suffix
        
        # Update the preview text widget
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", display_text)
        
        # Apply formatting
        if prefix:
            self.preview_text.tag_add("untyped", "1.0", f"1.3")
        if suffix:
            self.preview_text.tag_add("untyped", f"1.{len(prefix) + len(preview)}", "end")
            
        # Apply typed/untyped formatting
        if cursor_pos > 0:
            self.preview_text.tag_add("typed", "1.0", f"1.{cursor_pos}")
        
        if cursor_pos < len(display_text):
            self.preview_text.tag_add("untyped", f"1.{cursor_pos+1}", "end")
            
        # Apply cursor highlight
        if 0 <= cursor_pos < len(display_text):
            self.preview_text.tag_add("cursor", f"1.{cursor_pos}", f"1.{cursor_pos+1}")
            
        self.preview_text.config(state="disabled")
        
        # Store for animation
        self.typing_animation_chars = cursor_pos
    
    def type_text(self, text):
        """Main typing logic"""
        # Start countdown if needed
        countdown_seconds = self.countdown_var.get()
        if countdown_seconds > 0:
            self.status_var.set(f"Starting in {countdown_seconds}...")
            
            for i in range(countdown_seconds, 0, -1):
                if not self.is_typing:
                    return
                    
                self.status_var.set(f"Starting in {i}...")
                time.sleep(1)
                
        # Check if we're still typing

        if not self.is_typing:
            return
            
        # Give user time to switch applications
        if not self.is_paused:
            self.status_var.set("Switch to your target application now...")
            time.sleep(2)  # 2 second pause to switch applications
        
        # Force window to background to prevent focus stealing
        if platform.system() == 'Windows' and HAS_WIN32:
            try:
                win32gui.SetWindowPos(
                    win32gui.GetForegroundWindow(),
                    win32con.HWND_NOTOPMOST,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                )
            except:
                pass
            
        # Update status
        self.status_var.set("Typing...")        
        self.start_time = time.time()
        self.last_update_time = time.time()
        
        # Calculate base typing delay
        base_wpm = self.active_profile["base_wpm"]
        base_delay = 60 / (base_wpm * 5)
        
        # Get humanization settings
        variation_pct = self.active_profile["wpm_variation"] / 100
        error_rate = self.active_profile["error_rate"] / 100
        smart_pauses = self.active_profile["smart_pauses"]
        pause_multipliers = self.active_profile["pause_multiplier"]
        word_burst = self.active_profile["word_burst"]
        burst_prob = self.active_profile["burst_probability"]
        burst_multiplier = self.active_profile["burst_speed_multiplier"]
        rhythm = self.active_profile["typing_rhythm"]
        key_press_duration = self.active_profile["key_press_duration"]
        
        # Get thought pause settings
        thought_pause_enabled = self.thought_pause_var.get()
        thought_pause_prob = self.active_profile.get("thought_pause_probability", 0.08)
        thought_pause_duration = self.active_profile.get("thought_pause_duration", (0.8, 3.0))
        
        # Rhythm generators
        rhythm_generators = {
            "natural": lambda: random.normalvariate(1.0, 0.15),
            "consistent": lambda: random.uniform(0.95, 1.05),
            "irregular": lambda: random.choice([random.uniform(0.8, 0.9), random.uniform(1.0, 1.2)]),
            "ultra_natural": self.ultra_natural_rhythm
        }
        
        rhythm_gen = rhythm_generators.get(rhythm, lambda: 1.0)
        
        # Track word boundaries
        word_boundary = re.compile(r'\b')
        in_word = False
        bursting = False
        
        # Track control state for special key handling
        is_shift_down = False
        
        # Track WPM for display
        wpm_update_interval = 0.5  # Update WPM display every 0.5 seconds
        chars_since_update = 0
        
        # Start typing
        char_index = 0
        while char_index < len(text) and self.is_typing:
            # Handle pause state
            while self.is_paused and self.is_typing:
                time.sleep(0.1)
            
            # Check if we should still be typing
            if not self.is_typing:
                break
                
            # Get the current character
            current_char = text[char_index]
            
            # Update preview
            self.update_preview(text, char_index)
            
            # Determine if we're at a word boundary
            if word_boundary.search(text[char_index:char_index+1]):
                in_word = False
                bursting = False
            elif not in_word:
                in_word = True
                # Maybe start a burst
                bursting = word_burst and random.random() < burst_prob
            
            # Decide if we'll make an error
            will_make_error = random.random() < error_rate
            
            # Maybe take a thought pause (simulate thinking)
            if thought_pause_enabled and random.random() < thought_pause_prob:
                # Only pause at word boundaries or after punctuation
                if not in_word or current_char in ".,:;?!":
                    pause_time = random.uniform(
                        thought_pause_duration[0],
                        thought_pause_duration[1]
                    )
                    time.sleep(pause_time)
            
            try:
                # Handle character-specific typing behavior
                if will_make_error:
                    # Type incorrect character
                    error_char = self.generate_typo(current_char)
                    
                    # Check if character requires shift
                    if error_char.isupper() or error_char in '~!@#$%^&*()_+{}|:"<>?':
                        pyautogui.keyDown('shift')
                        is_shift_down = True
                        pyautogui.press(error_char.lower())
                    else:
                        pyautogui.press(error_char)
                    
                    # Play key sound
                    self.play_key_sound("key")
                    
                    # Release shift if needed
                    if is_shift_down:
                        pyautogui.keyUp('shift')
                        is_shift_down = False
                    
                    # Small pause after error
                    time.sleep(base_delay * random.uniform(0.5, 1.0))
                    
                    # Backspace to correct
                    pyautogui.press('backspace')
                    self.play_key_sound("key")
                    time.sleep(base_delay * random.uniform(0.8, 1.2))
                
                # Type the correct character
                if current_char == '\n':
                    pyautogui.press('enter')
                    self.play_key_sound("return")
                elif current_char == '\t':
                    pyautogui.press('tab')
                    self.play_key_sound("key")
                elif current_char == ' ':
                    pyautogui.press('space')
                    self.play_key_sound("space")
                elif current_char in '~!@#$%^&*()_+{}|:"<>?':
                    # Character requires shift
                    pyautogui.keyDown('shift')
                    is_shift_down = True
                    
                    # Map to base character
                    shift_map = {'~': '`', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0', '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\', ':': ';', '"': "'", '<': ',', '>': '.', '?': '/'}
                    pyautogui.press(shift_map[current_char])
                    self.play_key_sound("modifier")
                    
                    # Release shift
                    pyautogui.keyUp('shift')
                    is_shift_down = False
                elif current_char.isupper():
                    # Uppercase character needs shift
                    pyautogui.keyDown('shift')
                    is_shift_down = True
                    pyautogui.press(current_char.lower())
                    self.play_key_sound("key")
                    pyautogui.keyUp('shift')
                    is_shift_down = False
                else:
                    # Regular character
                    pyautogui.press(current_char)
                    self.play_key_sound("key")
                
                # Increment character counter
                char_index += 1
                self.chars_typed += 1
                chars_since_update += 1
                
                # Update progress
                progress_percent = (self.chars_typed / self.total_chars) * 100
                self.progress_var.set(progress_percent)
                self.progress_label.config(text=f"{self.chars_typed}/{self.total_chars} chars")
                
                # Update WPM display periodically
                current_time = time.time()
                if current_time - self.last_update_time >= wpm_update_interval:
                    # Calculate current WPM
                    total_time = current_time - self.start_time
                    current_wpm = int((self.chars_typed / 5) / (total_time / 60))
                    self.current_wpm_var.set(f"{current_wpm} WPM")
                    
                    # Reset counters
                    self.last_update_time = current_time
                    chars_since_update = 0
                
                # Calculate delay for next character
                delay = base_delay
                
                # Apply less aggressive rhythm variation
                if rhythm == "natural":
                    delay *= random.normalvariate(1.0, 0.08)  # Reduced from 0.15
                elif rhythm == "ultra_natural":
                    # Apply milder ultra_natural_rhythm
                    factor = self.ultra_natural_rhythm()
                    delay *= max(0.8, min(1.2, factor))  # Clamp values to prevent extremes
                else:
                    # Apply rhythm variation
                    delay *= rhythm_gen()
                
                # Apply burst speed if in a word burst (reduce strength)
                if bursting:
                    delay /= min(burst_multiplier, 1.3)  # Cap burst multiplier
                
                # Apply smart pauses for punctuation
                if smart_pauses and current_char in pause_multipliers:
                    delay *= pause_multipliers[current_char]
                
                # Limit the variation percentage impact
                if variation_pct > 0:
                    variation_factor = random.uniform(
                        max(0.9, 1 - variation_pct/2),  # Don't go below 90% speed
                        min(1.1, 1 + variation_pct/2)   # Don't go above 110% speed
                    )
                    delay *= variation_factor
                
                # More consistent minimum delay
                delay = max(0.005, delay)  # Higher minimum to avoid system limitations
                
                # Sleep before next character
                time.sleep(delay)
                
            except Exception as e:
                print(f"Typing error: {e}")
                # Try to ensure shift key is released if an error occurs
                if is_shift_down:
                    pyautogui.keyUp('shift')
                    is_shift_down = False
                    
                if self.is_typing:
                    self.queue.put(("error", str(e)))
                break
        
        # Ensure shift key is released
        if is_shift_down:
            pyautogui.keyUp('shift')
        
        # Signal completion
        if self.is_typing:
            self.queue.put(("complete", None))
    
    def generate_typo(self, char):
        """Generate a realistic typo for the given character"""
        # Define common typo patterns based on keyboard proximity
        keyboard_proximity = {
            'q': ['w', 'a'],
            'w': ['q', 'e', 's'],
            'e': ['w', 'r', 'd'],
            'r': ['e', 't', 'f'],
            't': ['r', 'y', 'g'],
            'y': ['t', 'u', 'h'],
            'u': ['y', 'i', 'j'],
            'i': ['u', 'o', 'k'],
            'o': ['i', 'p', 'l'],
            'p': ['o', '['],
            'a': ['q', 's', 'z'],
            's': ['w', 'a', 'd', 'x'],
            'd': ['e', 's', 'f', 'c'],
            'f': ['r', 'd', 'g', 'v'],
            'g': ['t', 'f', 'h', 'b'],
            'h': ['y', 'g', 'j', 'n'],
            'j': ['u', 'h', 'k', 'm'],
            'k': ['i', 'j', 'l'],
            'l': ['o', 'k', ';'],
            'z': ['a', 'x'],
            'x': ['z', 's', 'c'],
            'c': ['x', 'd', 'v'],
            'v': ['c', 'f', 'b'],
            'b': ['v', 'g', 'n'],
            'n': ['b', 'h', 'm'],
            'm': ['n', 'j', ','],
            ',': ['m', '.'],
            '.': [',', '/'],
            '/': ['.'],
            '1': ['2', '`'],
            '2': ['1', '3'],
            '3': ['2', '4'],
            '4': ['3', '5'],
            '5': ['4', '6'],
            '6': ['5', '7'],
            '7': ['6', '8'],
            '8': ['7', '9'],
            '9': ['8', '0'],
            '0': ['9', '-'],
            '-': ['0', '='],
            '=': ['-']
        }
        
        # Add uppercase mappings
        for k, v in list(keyboard_proximity.items()):
            if k.isalpha():
                keyboard_proximity[k.upper()] = [c.upper() for c in v if c.isalpha()]
        
        # Different typo strategies
        strategies = [
            # 1. Adjacent key error (most common)
            lambda c: random.choice(keyboard_proximity.get(c.lower(), [c])) if c.lower() in keyboard_proximity else c,
            
            # 2. Double character error
            lambda c: c + c,
            
            # 3. Character omission (we'll handle this by not generating an error)
            lambda c: c
        ]
        
        # Weighted choice of strategies
        weights = [0.7, 0.2, 0.1]
        strategy = random.choices(strategies, weights=weights)[0]
        
        return strategy(char)
    
    def ultra_natural_rhythm(self):
        """Generate ultra-realistic typing rhythm variations"""
        patterns = [
            # Steady typing (slight variations)
            lambda: random.normalvariate(1.0, 0.1),
            
            # Slight hesitation
            lambda: random.uniform(1.2, 1.5),
            
            # Quick burst
            lambda: random.uniform(0.7, 0.9),
            
            # Very short pauses (thinking)
            lambda: random.uniform(1.1, 1.3)
        ]
        
        # Weight toward natural typing with occasional variations
        weights = [0.6, 0.15, 0.15, 0.1]
        pattern = random.choices(patterns, weights=weights)[0]
        
        return pattern()
        
    def check_queue(self):
        """Check the queue for messages from the typing thread"""
        try:
            msg_type, data = self.queue.get_nowait()
            
            if msg_type == "complete":
                # Typing complete
                self.is_typing = False
                self.start_btn.config(state="normal")
                self.pause_btn.config(state="disabled")
                self.stop_btn.config(state="disabled")
                self.status_var.set("Completed")
                self.pause_btn.config(text="Pause")
                
                # Update status indicator
                self.update_status_indicator("stopped")
                
                # Calculate typing duration and speed
                if self.start_time > 0:
                    duration = time.time() - self.start_time
                    wpm = (self.chars_typed / 5) / (duration / 60)
                    self.status_var.set(f"Completed ({wpm:.1f} WPM)")
                    self.current_wpm_var.set(f"{int(wpm)} WPM")
                
                # Update status bar
                self.status_text.set(f"Typing completed at {int(wpm)} WPM")
                
                # Schedule status reset
                self.root.after(5000, lambda: self.status_text.set("Ready"))
            
            elif msg_type == "error":
                # Typing error
                self.is_typing = False
                self.start_btn.config(state="normal")
                self.pause_btn.config(state="disabled")
                self.stop_btn.config(state="disabled")
                self.status_var.set(f"Error")
                self.pause_btn.config(text="Pause")
                
                # Update status indicator
                self.update_status_indicator("stopped")
                
                # Update status bar
                self.status_text.set(f"Error: {data}")
                
                # Show error message
                messagebox.showerror("Typing Error", f"An error occurred during typing:\n{data}")
                
        except queue.Empty:
            pass
            
        # Schedule next check
        self.root.after(100, self.check_queue)
    
    def load_settings(self):
        """Load application settings"""
        settings_dir = os.path.join(os.path.expanduser("~"), ".stealthtyper")
        settings_file = os.path.join(settings_dir, "settings.json")
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                    
                # Update theme
                self.theme_mode = self.settings["theme"]
                
                # Update sound settings
                self.sound_enabled = self.settings["sound_enabled"]
        except Exception as e:
            print(f"Error loading settings: {e}")
            
        # Load profiles
        self.load_profiles_from_file()
    
    def save_settings(self):
        """Save application settings"""
        settings_dir = os.path.join(os.path.expanduser("~"), ".stealthtyper")
        
        try:
            os.makedirs(settings_dir, exist_ok=True)
            settings_file = os.path.join(settings_dir, "settings.json")
            
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def load_profiles_from_file(self):
        """Load typing profiles from file"""
        settings_dir = os.path.join(os.path.expanduser("~"), ".stealthtyper")
        profiles_file = os.path.join(settings_dir, "profiles.json")
        
        try:
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r') as f:
                    loaded_profiles = json.load(f)
                    
                    # Validate loaded profiles and update
                    for name, profile in loaded_profiles.items():
                        # Check for required fields
                        if all(k in profile for k in ["base_wpm", "pause_multiplier"]):
                            self.typing_profiles[name] = profile
        except Exception as e:
            print(f"Error loading profiles: {e}")
    
    def save_profiles_to_file(self):
        """Save typing profiles to file"""
        settings_dir = os.path.join(os.path.expanduser("~"), ".stealthtyper")
        
        try:
            os.makedirs(settings_dir, exist_ok=True)
            profiles_file = os.path.join(settings_dir, "profiles.json")
            
            with open(profiles_file, 'w') as f:
                json.dump(self.typing_profiles, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")
            messagebox.showerror("Error", f"Failed to save profiles: {str(e)}")

def main():
    # Check if we have admin rights on Windows (needed for global hotkeys)
    if platform.system() == 'Windows' and HAS_WIN32:
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if not is_admin:
                print("Warning: Running without admin rights may limit global hotkey functionality.")
        except:
            pass
    
    # Create main window
    root = tk.Tk()
    app = EnhancedStealthTyper(root)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()
       