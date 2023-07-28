import screen_utils
import config
import pygame
import random
import sys
from lines import lines
from spiro import spiro
from biomorph import biomorph
from hopalong import hopalong
from ifs import ifs
from newton import newton
from mandelbrot import mandelbrot
from lorenz import lorenz
from novaretti import novaretti
from flame import flame

def main():
    pygame.init()
    screen: screen_utils.Window = screen_utils.Window()
    if config.verbose:
        print(pygame.display.get_surface().get_size())
    running = True
    fractal_favored = ["mandelbrot", "flame", "ifs", "novaretti", "lorenz", "spiro", "lines", "hopalong", "biomorph",
                       "newton"]
    while running:
        if config.testing:
            mandelbrot(screen, 4)
        else:
            x = random.choice(fractal_favored)
            if x == "mandelbrot":
                mandelbrot(screen, 4)
                module_name = "Mandelbrot"
            elif x == "flame":
                flame(screen, 1)
                module_name = "Flame"
            elif x == "ifs":
                ifs(screen)
                module_name = "IFS"
            elif x == "novaretti":
                novaretti(screen, 1)
                module_name = "Novaretti"
            elif x == "lorenz":
                lorenz(screen)
                module_name = "Lorenz"
            elif x == "spiro":
                for _ in range(1):
                    spiro(screen)
                module_name = "Spiro"
            elif x == "lines":
                lines(screen)
                module_name = "Lines"
            elif x == "hopalong":
                for _ in range(1):
                    hopalong(screen)
                module_name = "Hopalong"
            elif x == "newton":
                newton(screen)
                module_name = "Newton"
            elif x == "biomorph":
                for _ in range(1):
                    biomorph(screen)
                module_name = "Biomorph"
            elif x == "flame":
                flame(screen, 1)
                module_name = "Flame"
            else:
                flame(screen, 1)
                module_name = "Flame"

            # Display the name of the current module
            pygame.display.set_caption('Fractals - ' + module_name)
            font = pygame.font.SysFont("Comic Sans MS", 30)
            text = font.render(module_name, True, pygame.Color("purple"))
            screen.surface.blit(text, (10, 10))
            pygame.display.flip()

        # Check for keyboard events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pygame.display.iconify()
                    print("Space key pressed. Minimizing window...")    
                elif event.key == pygame.K_DOWN:
                    pygame.display.iconify()
                    print("Down key pressed. Minimizing window...")
        
        screen.clock.tick(60)
        screen.clear()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")
        sys.exit(0)