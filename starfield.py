#!/usr/bin/env python3
import argparse
import random
import re
from PIL import Image, ImageDraw
import numpy as np


class StarfieldGenerator:
    def __init__(self, width, height, density, background):
        self.width = width
        self.height = height
        self.density = density
        self.background = background
        
    def parse_background(self):
        if self.background.startswith('#'):
            # Parse hex color
            hex_color = self.background.lstrip('#')
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return Image.new('RGB', (self.width, self.height), (r, g, b))
            else:
                raise ValueError(f"Invalid hex color: {self.background}")
        else:
            try:
                img = Image.open(self.background)
                if img.size != (self.width, self.height):
                    img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                return img.convert('RGB')
            except Exception as e:
                raise ValueError(f"Could not load background image: {e}")
    
    def generate_star_brightness(self):
        u = random.random()
        x_min = 1.0
        x_max = 10.0
        alpha = 5/2
        
        # Inverse CDF for power law
        r = random.random()
        brightness = (x_min**(-alpha + 1) + r * (x_max**(-alpha + 1) - x_min**(-alpha + 1)))**(1/(-alpha + 1))
        
        return brightness
    
    def draw_star(self, draw, x, y, brightness):
        intensity = int((brightness / 10.0) * 255)
        color = (intensity, intensity, intensity)
        
        if brightness < 3:
            draw.point((x, y), fill=color)
        elif brightness < 6:
            draw.ellipse([x-1, y-1, x+1, y+1], fill=color)
        else:
            radius = int(brightness / 5)
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color)
            if brightness > 8:
                glow_color = (intensity // 2, intensity // 2, intensity // 2)
                draw.ellipse([x-radius-1, y-radius-1, x+radius+1, y+radius+1], 
                           outline=glow_color)
    
    def draw_diffraction_spikes(self, img_array, x, y, brightness):
        if brightness <= 9:
            return
        spike_intensity = ((brightness - 9) / 1.0)
        base_intensity = int((brightness / 10.0) * 255)
        spike_length = int(8 + (brightness - 9) * 12)
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            for i in range(1, spike_length):
                px = x + dx * i
                py = y + dy * i
                
                if 0 <= px < self.width and 0 <= py < self.height:
                    fade = 1.0 - (i / spike_length)
                    spike_val = int(base_intensity * spike_intensity * fade)
                    current = img_array[py, px]
                    new_val = min(255, int(current[0]) + spike_val)
                    img_array[py, px] = [new_val, new_val, new_val]
        
        if brightness > 9.5:
            for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                for i in range(1, spike_length // 2):
                    px = x + dx * i
                    py = y + dy * i
                    
                    if 0 <= px < self.width and 0 <= py < self.height:
                        fade = 1.0 - (i / (spike_length // 2))
                        spike_val = int(base_intensity * spike_intensity * fade * 0.5)
                        
                        current = img_array[py, px]
                        new_val = min(255, int(current[0]) + spike_val)
                        img_array[py, px] = [new_val, new_val, new_val]
    
    def generate(self):
        img = self.parse_background()
        draw = ImageDraw.Draw(img)
        total_pixels = self.width * self.height
        num_stars = int(total_pixels * self.density)
        stars = []
        for _ in range(num_stars):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            brightness = self.generate_star_brightness()
            stars.append((x, y, brightness))
        for x, y, brightness in stars:
            self.draw_star(draw, x, y, brightness)
        img_array = np.array(img)
        for x, y, brightness in stars:
            if brightness > 8:
                self.draw_diffraction_spikes(img_array, x, y, brightness)
        img = Image.fromarray(img_array.astype('uint8'), 'RGB')
        
        return img


def parse_size(size_str):
    match = re.match(r'(\d+)[x:](\d+)', size_str)
    if not match:
        raise argparse.ArgumentTypeError(
            f"Size must be in format WIDTHxHEIGHT or WIDTH:HEIGHT (e.g., 1920x1080)"
        )
    width, height = int(match.group(1)), int(match.group(2))
    return width, height


def main():
    parser = argparse.ArgumentParser(
        description='Generate a starfield image'
    )
    
    parser.add_argument(
        '-s', '--size',
        type=str,
        default='1920x1080',
        help='Size of the image in pixels (format: WIDTHxHEIGHT or WIDTH:HEIGHT, default: 1920x1080)'
    )
    
    parser.add_argument(
        '-d', '--density',
        type=float,
        default=0.05,
        help='Ratio of star pixels to total pixels (0.0-1.0, default: 0.05)'
    )
    
    parser.add_argument(
        '-b', '--background',
        type=str,
        default='#000000',
        help='Background color (hex: #RRGGBB) or path to background image (default: #000000)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='starfield.png',
        help='Output file path (default: starfield.png)'
    )
    
    args = parser.parse_args()
    width, height = parse_size(args.size)
    if not 0.0 <= args.density <= 1.0:
        parser.error("Density must be between 0.0 and 1.0")
    print(f"Generating starfield: {width}x{height} with density {args.density}")
    generator = StarfieldGenerator(width, height, args.density, args.background)
    img = generator.generate()
    img.save(args.output)
    print(f"Starfield saved to {args.output}")


if __name__ == '__main__':
    main()
