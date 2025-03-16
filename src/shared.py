import pygame
import torch

# Check if CUDA is available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

# Initialize Pygame screen and clock
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Traffic Simulation")
clock = pygame.time.Clock()

def get_screen():
    """Get the Pygame screen"""
    return screen

def get_clock():
    """Get the Pygame clock"""
    return clock

def to_tensor(data, dtype=torch.float32):
    """Convert data to a tensor on the appropriate device"""
    if isinstance(data, (list, tuple)):
        return torch.tensor(data, dtype=dtype, device=DEVICE)
    return torch.tensor([data], dtype=dtype, device=DEVICE)

def to_numpy(tensor):
    """Convert a tensor to numpy array"""
    return tensor.cpu().numpy()

class PygameContext:
    """Class to manage shared Pygame resources"""
    instance = None
    
    def __init__(self, width, height):
        if PygameContext.instance is not None:
            raise Exception("PygameContext already initialized")
            
        # Initialize Pygame
        pygame.init()
        
        # Create the screen
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Traffic Simulation")
        
        # Create clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
        # Set as singleton instance
        PygameContext.instance = self
    
    @staticmethod
    def get_instance():
        if PygameContext.instance is None:
            raise Exception("PygameContext not initialized")
        return PygameContext.instance

    @staticmethod
    def init(width, height):
        """Initialize the Pygame context if not already initialized"""
        if PygameContext.instance is None:
            PygameContext(width, height)
        return PygameContext.instance

# Shorthand functions to get screen and clock
def get_screen():
    return PygameContext.get_instance().screen
    
def get_clock():
    return PygameContext.get_instance().clock 