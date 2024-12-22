import pygame 

class Button:
    def __init__(self, image, pos, text_input, font, base_color, hovering_color, border_color=(0,0,0), border_width=2):
        self.image = image
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.font = font
        self.base_color, self.hovering_color = base_color, hovering_color
        self.text_input = text_input
        self.text = self.font.render(self.text_input, True, self.base_color)
        if self.image is None:
            self.image = self.text
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))
        self.border_color = border_color
        self.border_width = border_width

    def update(self, screen):
        if self.image is not None:
            screen.blit(self.image, self.rect)

        # Create a semi-transparent rectangle
        button_surface = pygame.Surface((self.rect.width + 20, self.rect.height + 20))
        button_surface.set_alpha(150)
        button_surface.fill((100, 100, 100))  # Gray color

        # Draw the semi-transparent rectangle
        screen.blit(button_surface, (self.rect.x - 10, self.rect.y - 10))

        # Draw the border
        pygame.draw.rect(screen, self.border_color, (self.rect.x - 10, self.rect.y - 10, 
                         self.rect.width + 20, self.rect.height + 20), self.border_width)

        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            return True
        return False

    def changeColor(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            self.text = self.font.render(self.text_input, True, self.hovering_color)
        else:
            self.text = self.font.render(self.text_input, True, self.base_color)