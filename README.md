 <code>demospy</code> has these immediate goals:
  - present the Desmos API with consistent terminology
  - keep it simple, keep it pythonic

Basic usage is very simple.  Create an instance of <code>Calculator</code>, then assign to one of its members.


```python
from desmospy import Calculator

c = Calculator()
c.y = 1/2 * c.x + 3
c.show()
```



<iframe
    width="720"
    height="360"
    src="data:text/html;base64,Cjxib2R5IHN0eWxlPSJiYWNrZ3JvdW5kLWNvbG9yOiMyQTJBMkE7IiBtYXJnaW53aWR0aD0iMHB4IiBtYXJnaW5oZWlnaHQ9IjBweCI+CjxzY3JpcHQgc3JjPSJodHRwczovL3d3dy5kZXNtb3MuY29tL2FwaS92MS45L2NhbGN1bGF0b3IuanM/YXBpS2V5PWRjYjMxNzA5YjQ1MmIxY2Y5ZGMyNjk3MmFkZDBmZGE2Ij48L3NjcmlwdD4KPGRpdiBpZD0iY2FsY3VsYXRvciI+PC9kaXY+CjxzY3JpcHQ+Cgl2YXIgZWx0ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImNhbGN1bGF0b3IiKTsKCXZhciBjYWxjdWxhdG9yID0gRGVzbW9zLkdyYXBoaW5nQ2FsY3VsYXRvcihlbHQsIG9wdGlvbnM9e30pOwoJY2FsY3VsYXRvci5zZXRFeHByZXNzaW9uKHsKCQlsYXRleDogJ3kgPSAwLjUgeCArIDMnLAoJCWlkOiAnMCcsCgl9KTsKCjwvc2NyaXB0Pgo="
    frameborder="0"
    allowfullscreen

></iframe>



More advanced plots can be created with comparisons and the <code>.define()</code> method:


```python
c.a = 0.3
a,x,y = c.a,c.x,c.y

c.define(y < a*x)
c.define(y >= a*x**2)
c.define(a*x*y == 1)
c.show()
```



<iframe
    width="720"
    height="360"
    src="data:text/html;base64,Cjxib2R5IHN0eWxlPSJiYWNrZ3JvdW5kLWNvbG9yOiMyQTJBMkE7IiBtYXJnaW53aWR0aD0iMHB4IiBtYXJnaW5oZWlnaHQ9IjBweCI+CjxzY3JpcHQgc3JjPSJodHRwczovL3d3dy5kZXNtb3MuY29tL2FwaS92MS45L2NhbGN1bGF0b3IuanM/YXBpS2V5PWRjYjMxNzA5YjQ1MmIxY2Y5ZGMyNjk3MmFkZDBmZGE2Ij48L3NjcmlwdD4KPGRpdiBpZD0iY2FsY3VsYXRvciI+PC9kaXY+CjxzY3JpcHQ+Cgl2YXIgZWx0ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImNhbGN1bGF0b3IiKTsKCXZhciBjYWxjdWxhdG9yID0gRGVzbW9zLkdyYXBoaW5nQ2FsY3VsYXRvcihlbHQsIG9wdGlvbnM9e30pOwoJY2FsY3VsYXRvci5zZXRFeHByZXNzaW9uKHsKCQlsYXRleDogJ2EgPSAwLjMnLAoJCWlkOiAnMCcsCgl9KTsKCmNhbGN1bGF0b3Iuc2V0RXhwcmVzc2lvbih7CgkJbGF0ZXg6ICd5IFxcbHQgYSB4JywKCQlpZDogJzEnLAoJfSk7CgpjYWxjdWxhdG9yLnNldEV4cHJlc3Npb24oewoJCWxhdGV4OiAneSBcXGdlIGEgeF57Mn0nLAoJCWlkOiAnMicsCgl9KTsKCmNhbGN1bGF0b3Iuc2V0RXhwcmVzc2lvbih7CgkJbGF0ZXg6ICdhIHggeSA9IDEnLAoJCWlkOiAnMycsCgl9KTsKCjwvc2NyaXB0Pgo="
    frameborder="0"
    allowfullscreen

></iframe>



Equations and inequalities can also be combined; first let's define two ellipse regions.


```python
A = (x**2 / 49 + y**2 / 16 <= 1)
B = (x**2 / 16 + y**2 / 49 <= 1)
```

We can then take the union, also known as a logical OR <code>|</code> of the regions.


```python
c.define(A | B)
c.show()
```



<iframe
    width="720"
    height="360"
    src="data:text/html;base64,Cjxib2R5IHN0eWxlPSJiYWNrZ3JvdW5kLWNvbG9yOiMyQTJBMkE7IiBtYXJnaW53aWR0aD0iMHB4IiBtYXJnaW5oZWlnaHQ9IjBweCI+CjxzY3JpcHQgc3JjPSJodHRwczovL3d3dy5kZXNtb3MuY29tL2FwaS92MS45L2NhbGN1bGF0b3IuanM/YXBpS2V5PWRjYjMxNzA5YjQ1MmIxY2Y5ZGMyNjk3MmFkZDBmZGE2Ij48L3NjcmlwdD4KPGRpdiBpZD0iY2FsY3VsYXRvciI+PC9kaXY+CjxzY3JpcHQ+Cgl2YXIgZWx0ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImNhbGN1bGF0b3IiKTsKCXZhciBjYWxjdWxhdG9yID0gRGVzbW9zLkdyYXBoaW5nQ2FsY3VsYXRvcihlbHQsIG9wdGlvbnM9e30pOwoJY2FsY3VsYXRvci5zZXRFeHByZXNzaW9uKHsKCQlsYXRleDogJ21heCgtIFxcZnJhY3t4XnsyfX17NDl9IC0gXFxmcmFje3leezJ9fXsxNn0gKyAxLCAtIFxcZnJhY3t4XnsyfX17MTZ9IC0gXFxmcmFje3leezJ9fXs0OX0gKyAxKSBcXGdlIDAnLAoJCWlkOiAnMCcsCgl9KTsKCjwvc2NyaXB0Pgo="
    frameborder="0"
    allowfullscreen

></iframe>



We can also take the intersection of the same regions, with the logical AND <code>&</code> operation.


```python
c.define(A & B)
c.show()
```



<iframe
    width="720"
    height="360"
    src="data:text/html;base64,Cjxib2R5IHN0eWxlPSJiYWNrZ3JvdW5kLWNvbG9yOiMyQTJBMkE7IiBtYXJnaW53aWR0aD0iMHB4IiBtYXJnaW5oZWlnaHQ9IjBweCI+CjxzY3JpcHQgc3JjPSJodHRwczovL3d3dy5kZXNtb3MuY29tL2FwaS92MS45L2NhbGN1bGF0b3IuanM/YXBpS2V5PWRjYjMxNzA5YjQ1MmIxY2Y5ZGMyNjk3MmFkZDBmZGE2Ij48L3NjcmlwdD4KPGRpdiBpZD0iY2FsY3VsYXRvciI+PC9kaXY+CjxzY3JpcHQ+Cgl2YXIgZWx0ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImNhbGN1bGF0b3IiKTsKCXZhciBjYWxjdWxhdG9yID0gRGVzbW9zLkdyYXBoaW5nQ2FsY3VsYXRvcihlbHQsIG9wdGlvbnM9e30pOwoJY2FsY3VsYXRvci5zZXRFeHByZXNzaW9uKHsKCQlsYXRleDogJ21pbigtIFxcZnJhY3t4XnsyfX17NDl9IC0gXFxmcmFje3leezJ9fXsxNn0gKyAxLCAtIFxcZnJhY3t4XnsyfX17MTZ9IC0gXFxmcmFje3leezJ9fXs0OX0gKyAxKSBcXGdlIDAnLAoJCWlkOiAnMCcsCgl9KTsKCjwvc2NyaXB0Pgo="
    frameborder="0"
    allowfullscreen

></iframe>



This leaves the logical XOR <code>^</code> operation.


```python
c.define(A ^ B)
c.show()
```



<iframe
    width="720"
    height="360"
    src="data:text/html;base64,Cjxib2R5IHN0eWxlPSJiYWNrZ3JvdW5kLWNvbG9yOiMyQTJBMkE7IiBtYXJnaW53aWR0aD0iMHB4IiBtYXJnaW5oZWlnaHQ9IjBweCI+CjxzY3JpcHQgc3JjPSJodHRwczovL3d3dy5kZXNtb3MuY29tL2FwaS92MS45L2NhbGN1bGF0b3IuanM/YXBpS2V5PWRjYjMxNzA5YjQ1MmIxY2Y5ZGMyNjk3MmFkZDBmZGE2Ij48L3NjcmlwdD4KPGRpdiBpZD0iY2FsY3VsYXRvciI+PC9kaXY+CjxzY3JpcHQ+Cgl2YXIgZWx0ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImNhbGN1bGF0b3IiKTsKCXZhciBjYWxjdWxhdG9yID0gRGVzbW9zLkdyYXBoaW5nQ2FsY3VsYXRvcihlbHQsIG9wdGlvbnM9e30pOwoJY2FsY3VsYXRvci5zZXRFeHByZXNzaW9uKHsKCQlsYXRleDogJy0oLSBcXGZyYWN7eF57Mn19ezQ5fSAtIFxcZnJhY3t5XnsyfX17MTZ9ICsgMSkqKC0gXFxmcmFje3heezJ9fXsxNn0gLSBcXGZyYWN7eV57Mn19ezQ5fSArIDEpIFxcZ2UgMCcsCgkJaWQ6ICcwJywKCX0pOwoKPC9zY3JpcHQ+Cg=="
    frameborder="0"
    allowfullscreen

></iframe>


