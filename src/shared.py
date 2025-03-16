import pygame
import torch

# Check if CUDA is available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

def to_tensor(data, dtype=torch.float32):
    """Convert data to a tensor on the appropriate device"""
    if isinstance(data, (list, tuple)):
        return torch.tensor(data, dtype=dtype, device=DEVICE)
    return torch.tensor([data], dtype=dtype, device=DEVICE)

def to_numpy(tensor):
    """Convert a tensor to numpy array"""
    return tensor.cpu().numpy()

class PygameContext:
    _screen = None
    _clock = None

    @classmethod
    def initialize(cls, screen):
        """Initialize the Pygame context with a screen"""
        cls._screen = screen
        cls._clock = pygame.time.Clock()

    @classmethod
    def get_screen(cls):
        """Get the Pygame screen surface"""
        if cls._screen is None:
            raise RuntimeError("PygameContext not initialized. Call initialize() first.")
        return cls._screen

    @classmethod
    def get_clock(cls):
        """Get the Pygame clock"""
        if cls._clock is None:
            raise RuntimeError("PygameContext not initialized. Call initialize() first.")
        return cls._clock

def get_screen():
    """Get the current Pygame screen surface"""
    return PygameContext.get_screen()

def get_clock():
    """Get the current Pygame clock"""
    return PygameContext.get_clock() 