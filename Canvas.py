
from __future__ import annotations

from typing import List
from abc import ABC, abstractmethod

import time
import tkinter
from PIL import Image, ImageTk

#TODO add some telemetry log class that can have child logs. When telemetry measures, 
# it adds this proces to a list of ongoing processes, and the resulting log as a child to each ongoing proces.
# Thus we can display what processes compound a certain process.

class Log:
	children: List[Log] = []
	records: List[float] = []

	def __init__(self, name: str):
		self.name = name

	def record(self, delta: float):
		self.records.append(delta)

	def inside(self, log: Log):
		if log not in self.children:
			self.children.append(log)
			
	def average(self) -> float:
		return round(sum(self.records) / len(self.records), 3)

	def report(self) -> str:
		report = f'{ self.name }: { self.average() }s'

		index = 0
		while index < len(self.children):
			if index == len(self.children) - 1:
				report += '\n └─ ' + self.children[index].report().replace('\n', '\n  ')
			else:
				report += '\n ├─ ' + self.children[index].report().replace('\n', '\n │ ')
			index += 1

		return report

class Telemetry:
	roots = []
	logs: dict[callable, Log] = {}

	def measure(self, name: str | None = None, callback: callable | None = None):
		if callback is not None:
			if callback not in self.logs:
				self.logs[callback] = Log(name if name else callback.__name__)
				self.roots.append(self.logs[callback])

			start = time.time()
			callback()
			end = time.time()

			self.logs[callback].record(end - start)

			return

		def decorator(func: callable):
			if func not in self.logs:
				self.logs[func] = Log(name if name else func.__name__)
				self.roots.append(self.logs[func])

			def wrapper(*args, **kwargs):
				start = time.time()
				result = func(*args, **kwargs)
				end = time.time()

				self.logs[func].record(end - start)
	
				return result
			return wrapper
		return decorator

	def report(self):
		print('Telemetry Report')
		for log in self.logs.values():
			print(log.report())

class Canvas:
	telemetry = Telemetry()
	objects: List[Object] = []

	def __init__(self, width: int, height: int, title: str = 'Canvas'):
		self.width = width
		self.height = height
		self.title = title
		self.pixels = [[Color() for _ in range(self.width)] for _ in range(self.height)]

	@telemetry.measure()
	def show(self):
		tk = tkinter.Tk()
		tk.title(self.title)

		canvas.draw()
		img = Image.new('RGB', (self.width, self.height))
		pixels = [color.rgb for row in self.pixels for color in row]
		img.putdata(pixels)
		
		img_tk = ImageTk.PhotoImage(img)
		label = tkinter.Label(tk, image=img_tk)
		label.pack()

		tk.mainloop()
	
	@telemetry.measure()
	def draw(self):
		self.objects.sort(key=lambda obj: obj.layer)
		for obj in self.objects:
			self.telemetry.measure('Object', lambda: obj.draw(self))

	def add(self, obj: Object):
		self.objects.append(obj)

class Color:
	def __init__(self, red: int = 255, green: int = 255, blue: int = 255, alpha: float = 1.0, *, hex: str | None = None):
		self.red   = red
		self.green = green
		self.blue  = blue
		self.alpha = alpha
		
		if (hex != None): 
			self.hex = hex

	@property
	def rgb(self):
		return (self.red, self.green, self.blue)
	
	@rgb.setter
	def rgb(self, value: tuple[int, int, int]):
		self.red, self.green, self.blue = value

	@property
	def hex(self):
		return '#{:02x}{:02x}{:02x}'.format(self.red, self.green, self.blue)
	
	@hex.setter
	def hex(self, value: str):
		if len(value) == 7:
			self.red = int(value[1:3], 16)
			self.green = int(value[3:5], 16)
			self.blue = int(value[5:7], 16)
		
		elif len(value) == 4:
			self.red = int(value[1] * 2, 16)
			self.green = int(value[2] * 2, 16)
			self.blue = int(value[3] * 2, 16)

	def blend(self, other: Color) -> Color:
		red = int(self.red * self.alpha + other.red * (1 - self.alpha))
		green = int(self.green * self.alpha + other.green * (1 - self.alpha))
		blue = int(self.blue * self.alpha + other.blue * (1 - self.alpha))

		return Color(red, green, blue)

class Object(ABC):
	layer: int = 0

	@abstractmethod
	def draw(self, canvas: Canvas):
		pass

class Rectangle(Object):
	background_color: Color = Color(alpha=0.0)
	border_color: Color = Color(hex='#000')
	border_width: int = 1

	def __init__(self, x: int, y: int, width: int, height: int):
		self.x = x
		self.y = y
		self.width = width
		self.height = height

	def draw(self, canvas: Canvas):
		for y in range(self.y, self.y + self.height):
			for x in range(self.x, self.x + self.width):
				if (y == self.y or y == self.y + self.height - 1 or x == self.x or x == self.x + self.width - 1):
					canvas.pixels[y][x] = self.border_color.blend(canvas.pixels[y][x])
				else:
					canvas.pixels[y][x] = self.background_color.blend(canvas.pixels[y][x])

canvas = Canvas(1000, 1000)
rectangle = Rectangle(200, 200, 600, 600)
canvas.add(rectangle)
canvas.show()
canvas.telemetry.report()
