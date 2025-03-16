import pygame

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